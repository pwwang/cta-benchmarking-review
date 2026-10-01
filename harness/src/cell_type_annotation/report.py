# --------------------------------------------------------------------------
# WHAT   Reporting pipeline: walks the pipeline working directories and writes
#        pipelines.json summarising each run.
# REVIEW Provenance / audit trail for the arm runs; produces no cited number.
# SOURCE harness/src/cell_type_annotation/report.py
# --------------------------------------------------------------------------
from pipen import run
from biopipen.core.proc import Proc
from biopipen.core.config import config


class WorkingDir(Proc):
    """Take the working directory of the pipelines and output a json file
    with the parsed information of the pipelines.
    """
    input = "indir:dir"
    output = "outfile:file:pipelines.json"
    lang = config.lang.python
    script = """
        from pathlib import Path
        import json

        indir = Path({{in.indir | quote}})
        outfile = Path({{out.outfile | quote}})

        output = {}
        for pipeline in indir.iterdir():
            if not pipeline.is_dir():
                continue

            dataset = pipeline.name.split("_", 1)[-1]
            output[dataset] = {}
            for proc in pipeline.iterdir():
                if not proc.is_dir() or not proc.name.startswith("CellTypeAnnotation"):
                    continue

                parts = proc.name.split("_")[1:]
                ref = parts[-1]
                tool = "_".join(parts[:-1])
                output[dataset][f"{tool} / {ref}"] = {}
                # parse runinfo.time
                runinfo_file = proc / "0" / "job.runinfo.time"
                # get the Elapsed real time (s): 16.94
                with runinfo_file.open() as f:
                    for line in f:
                        if line.startswith("Elapsed real time (s):"):
                            output[dataset][f"{tool} / {ref}"]["time"] = float(
                                line.split(":")[1].strip()
                            ) / 60.0  # convert to minutes
                        elif line.startswith("Maximum resident set size (kB):"):
                            output[dataset][f"{tool} / {ref}"]["memory"] = int(
                                line.split(":")[1].strip()
                            ) / 1024.0  # convert to MB

        with outfile.open("w") as f:
            json.dump(output, f, indent=4)
    """


class Report(Proc):
    """Generate a report of the pipelines."""
    requires = WorkingDir
    input = "infile:file"
    output = "outdir:dir:report"
    lang = config.lang.rscript
    script = """
        library(plotthis)
        library(jsonlite)
        library(biopipen.utils)

        reporter <- get_reporter()

        infile <- {{in.infile | quote}}
        outdir <- {{out.outdir | quote}}
        joboutdir <- {{job.outdir | quote}}

        data <- fromJSON(infile)

        # convert data to a data frame
        df <- do.call(rbind, lapply(names(data), function(dataset) {
            do.call(rbind, lapply(names(data[[dataset]]), function(tool_ref) {
                cbind(
                    dataset = dataset,
                    tool_ref = tool_ref,
                    time = data[[dataset]][[tool_ref]]$time,
                    memory = data[[dataset]][[tool_ref]]$memory)
            }))
        }))
        df <- as.data.frame(df)
        df$time <- as.numeric(df$time)
        df$memory <- as.numeric(df$memory)

        datasets <- unique(df$dataset)
        for (dataset in datasets) {
            df_subset <- df[df$dataset == dataset, , drop = FALSE]
            p_time <- BarPlot(
                df_subset,
                x = "tool_ref",
                y = "time",
                x_text_angle = 90,
                xlab = "",
                ylab = "Time (min)",
                legend.position = "none",
                title = paste("Running Time for", dataset)
            )
            p_memory <- BarPlot(
                df_subset,
                x = "tool_ref",
                y = "memory",
                x_text_angle = 90,
                xlab = "",
                ylab = "Peak Memory (MB)",
                legend.position = "none",
                title = paste("Peak Memory for", dataset)
            )
            time_plot <- file.path(outdir, paste0(dataset, "_time.png"))
            memory_plot <- file.path(outdir, paste0(dataset, "_memory.png"))
            ggplot2::ggsave(time_plot, p_time)
            ggplot2::ggsave(memory_plot, p_memory)

            reporter$add(
                list(
                    kind = "image",
                    src = time_plot
                ),
                h1 = dataset,
                h2 = "Running Time"
            )

            reporter$add(
                list(
                    kind = "image",
                    src = memory_plot
                ),
                h1 = dataset,
                h2 = "Peak Memory"
            )
        }

        reporter$save(joboutdir)
    """
    plugin_opts = {
        "report": """
            {% macro report_jobs(jobs, job_head_macro, job_report_macro) %}

            {% if len(jobs) == 1 %}

            {{  job_report_macro(jobs[0], h=1) }}

            {% else %}

            {%  for job in jobs %}
            {{      job_head_macro(job)}}
            {{      job_report_macro(job, h=2) }}
            {%  endfor %}

            {% endif %}
            {% endmacro %}

            <script>
                import { Image, DataTable, Descr, Plotly } from "$libs";
                import { Tabs, Tab, TabContent, UnorderedList, ListItem, InlineNotification } from "$ccs";
            </script>

            {%- macro report_job(job, h=1) -%}
                {{ job | render_job: h=h }}
            {%- endmacro -%}

            {%- macro head_job(job) -%}
                <h1>{{job.in | attr: "values" | call | first | stem0 | escape}}</h1>
            {%- endmacro -%}

            {{ report_jobs(jobs, head_job, report_job) }}
        """
    }


if __name__ == "__main__":
    run("Report", starts=WorkingDir, data=[".pipen"], outdir="./report")
