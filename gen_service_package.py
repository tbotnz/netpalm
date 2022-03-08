import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='netpalm service package generate')
    required_files = parser.add_argument_group('required arguments')
    required_files.add_argument('-n', '--name', help='service package name', required=True)
    required_files.add_argument('-o', '--output', help='python | base64', default="python", required=True)
    args = parser.parse_args()

    package_name = args.name.replace(" ", "_")

    if os.path.isdir(package_name) or os.path.isfile(package_name):
        print("Please use a different package name, this is in use already")
        exit()

    os.mkdir(package_name)



example_service = """
"""

    with open(f'{package_name}.py', 'w') as fp:
        pass
