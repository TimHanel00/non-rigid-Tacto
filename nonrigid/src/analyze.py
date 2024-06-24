import argparse
from core.dataset import Dataset

def analyze( data_path ):
    dataset = Dataset( data_path )
    dataset.print_state()
    dataset.print_all_issues()
    dataset.count_issues_per_block()
    #dataset.print_md5sums()


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Analyze dataset",
            description="Tool to analyze the generated data after running a pipeline")

    parser.add_argument("--data_path", type=str, default="data")
    parser.add_argument("--sample_id", type=int)

    args = parser.parse_args()

    analyze( args.data_path )


