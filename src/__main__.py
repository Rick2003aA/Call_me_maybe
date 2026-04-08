from .cli import cli
from .errors import AppError
from .orchestrator import run_pipeline


def main():
    try:
        args = cli()
        run_pipeline(args)
    except AppError as e:
        print(e)


if __name__ == "__main__":
    main()
