use clap::{Parser, Subcommand};
use nirs4all_domains::structure::{
    characterize_structure, structure_markdown, StructureConfig, StructureReport,
};
use nirs4all_domains::{
    analyze, comparison_task, markdown, train_refit_stability, validate, Report, Task,
};
use std::{
    path::{Path, PathBuf},
    process::{Command, ExitCode},
};

#[derive(Parser)]
#[command(
    name = "n4domains",
    version,
    about = "Explicit NIRS train/test scientific audits"
)]
struct Args {
    #[command(subcommand)]
    command: Action,
}
#[derive(Subcommand)]
enum Action {
    Structure {
        task: PathBuf,
        #[arg(long)]
        config: PathBuf,
        #[arg(long)]
        out: PathBuf,
        #[arg(long, env = "N4DOMAINS_METHODS_LIBRARY")]
        methods_library: Option<PathBuf>,
    },
    Stability {
        task: PathBuf,
        #[arg(long)]
        out: PathBuf,
        #[arg(long, default_value_t = 100)]
        draws: usize,
        #[arg(long, env = "N4DOMAINS_METHODS_LIBRARY")]
        methods_library: PathBuf,
    },
    Represent {
        task: PathBuf,
        #[arg(long)]
        out: PathBuf,
        #[arg(long, env = "N4DOMAINS_METHODS_LIBRARY")]
        methods_library: PathBuf,
    },
    Validate {
        task: PathBuf,
    },
    Analyze {
        task: PathBuf,
        #[arg(long)]
        out: PathBuf,
        #[arg(long, env = "N4DOMAINS_METHODS_LIBRARY")]
        methods_library: Option<PathBuf>,
    },
    Schema {
        #[arg(long)]
        out: PathBuf,
    },
    Batch {
        #[arg(long)]
        catalog_config: PathBuf,
        #[arg(long)]
        catalog_root: Option<PathBuf>,
        #[arg(long)]
        out: PathBuf,
        #[arg(long, default_value = "python")]
        python: String,
        #[arg(long, env = "N4DOMAINS_METHODS_LIBRARY")]
        methods_library: Option<PathBuf>,
    },
}
fn read(path: &Path) -> Result<Task, String> {
    if std::fs::metadata(path).map_err(|e| e.to_string())?.len() > 256_000_000 {
        return Err("TASK_FILE_BUDGET_EXCEEDED".into());
    }
    let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
    serde_json::from_slice(&bytes).map_err(|e| e.to_string())
}
fn run() -> Result<u8, String> {
    match Args::parse().command {
        Action::Structure {
            task,
            config,
            out,
            methods_library,
        } => {
            let task = read(&task)?;
            if std::fs::metadata(&config).map_err(|e| e.to_string())?.len() > 64_000 {
                return Err("STRUCTURE_CONFIG_FILE_BUDGET_EXCEEDED".into());
            }
            let config: StructureConfig =
                serde_json::from_slice(&std::fs::read(config).map_err(|e| e.to_string())?)
                    .map_err(|e| e.to_string())?;
            config.validate()?;
            if let Some(parent) = out.parent().filter(|p| !p.as_os_str().is_empty()) {
                std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            std::fs::create_dir(&out)
                .map_err(|e| format!("A new structural output directory is required: {e}"))?;
            let report = characterize_structure(&task, &config, methods_library.as_deref());
            std::fs::write(
                out.join("report.json"),
                serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?,
            )
            .map_err(|e| e.to_string())?;
            std::fs::write(out.join("report.md"), structure_markdown(&report))
                .map_err(|e| e.to_string())?;
            println!(
                "{}: {:?} / {:?}",
                report.context.dataset_id, report.status, report.classification
            );
            Ok(if report.status == nirs4all_domains::Status::Error {
                2
            } else {
                0
            })
        }
        Action::Stability {
            task,
            out,
            draws,
            methods_library,
        } => {
            let result = train_refit_stability(&read(&task)?, &methods_library, draws)?;
            let mut file = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(out)
                .map_err(|e| e.to_string())?;
            serde_json::to_writer_pretty(&mut file, &result).map_err(|e| e.to_string())?;
            Ok(0)
        }
        Action::Represent {
            task,
            out,
            methods_library,
        } => {
            let task = comparison_task(&read(&task)?, &methods_library)?;
            let mut file = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(out)
                .map_err(|e| e.to_string())?;
            serde_json::to_writer(&mut file, &task).map_err(|e| e.to_string())?;
            Ok(0)
        }
        Action::Validate { task } => {
            validate(&read(&task)?)?;
            println!("valid");
            Ok(0)
        }
        Action::Analyze {
            task,
            out,
            methods_library,
        } => {
            let report = analyze(&read(&task)?, methods_library.as_deref());
            std::fs::create_dir_all(&out).map_err(|e| e.to_string())?;
            std::fs::write(
                out.join("report.json"),
                serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?,
            )
            .map_err(|e| e.to_string())?;
            std::fs::write(out.join("report.md"), markdown(&report)).map_err(|e| e.to_string())?;
            println!("{}: {}", report.context.dataset_id, report.status);
            Ok(if report.status == "failed" { 2 } else { 0 })
        }
        Action::Schema { out } => {
            std::fs::create_dir_all(&out).map_err(|e| e.to_string())?;
            for (name, schema) in [
                ("task.v1.schema.json", schemars::schema_for!(Task)),
                ("report.v1.schema.json", schemars::schema_for!(Report)),
                (
                    "structure-config.v1.schema.json",
                    schemars::schema_for!(StructureConfig),
                ),
                (
                    "structure-report.v1.schema.json",
                    schemars::schema_for!(StructureReport),
                ),
            ] {
                std::fs::write(
                    out.join(name),
                    serde_json::to_vec_pretty(&schema).map_err(|e| e.to_string())?,
                )
                .map_err(|e| e.to_string())?;
            }
            Ok(0)
        }
        Action::Batch {
            catalog_config,
            catalog_root,
            out,
            python,
            methods_library,
        } => {
            let mut cmd = Command::new(python);
            cmd.args(["-m", "nirs4all_domains.batch", "--catalog-config"])
                .arg(catalog_config)
                .arg("--out")
                .arg(out)
                .env(
                    "N4DOMAINS_BIN",
                    std::env::current_exe().map_err(|e| e.to_string())?,
                );
            if let Some(path) = methods_library {
                cmd.arg("--methods-library").arg(path);
            }
            if let Some(path) = catalog_root {
                cmd.arg("--catalog-root").arg(path);
            }
            let status = cmd
                .status()
                .map_err(|e| format!("Python bridge unavailable: {e}; install bridges/python"))?;
            Ok(status.code().unwrap_or(2) as u8)
        }
    }
}
fn main() -> ExitCode {
    match run() {
        Ok(code) => ExitCode::from(code),
        Err(e) => {
            eprintln!("n4domains: {e}");
            ExitCode::from(2)
        }
    }
}
