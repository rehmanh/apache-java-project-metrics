import subprocess
import shutil
import csv
import ApacheProjectRepos
from datetime import datetime

BASE_URL = 'https://github.com/apache'

class ApacheMetricCollection:
    def __init__(self) -> None:
        pass

    def generate_project_repo_list(self) -> list:
        obj = ApacheProjectRepos.ApacheProjectRepos()
        #obj = TestApacheRepos.TestApacheRepos()
        repo_names = [getattr(obj, x) for x in dir(obj) if not x.startswith("__")]
        repos = []
        for repo_name in repo_names:
            tup = (repo_name, f"{BASE_URL}/{repo_name}.git")
            repos.append(tup)
        return repos

    def clone_and_process_gh_repos(self, repos: list) -> None:
        for repo in repos:
            name = repo[0]
            url = repo[1]

            process = subprocess.Popen(
                ["git", "clone", url, name], 
                cwd="./repositories", 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print(f"Cloning the project {name}...")
            process.wait()

            # check the output and error of the clone command
            output, error = process.communicate()

            if (process.poll() == 0):
                # clone successful -- want to begin processing the gitlog files
                num_revisions = self.get_project_revision_count(name)
                num_authors = self.get_project_author_count(name)
                num_source_files = self.get_num_source_files(name)
                num_source_loc = self.get_source_loc(name)
                first_revision_date = self.get_first_commit_date(name)
                self.write_data_to_csv(name, num_revisions, num_authors, num_source_files, num_source_loc, first_revision_date)
            elif(process.poll() == 128):
                # clone unsuccessful -- print error and continue
                print(f"Repository for project {name} was not found on GitHub")
                self.write_data_to_csv(name, 0, 0, 0, 0, 0)

            print(f"Collected metrics for {name}; removing the directory ./repositories/{name}...\n")
            self.remove_repo_directory(name)
                

    def get_project_revision_count(self, dir_name: str) -> int:
        process = subprocess.Popen(
            ["git", "rev-list", "--count", "HEAD"], # fetch number of commits on HEAD
            cwd=f"./repositories/{dir_name}",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.wait()
        output, error = process.communicate()
        if error == "":
            return int(output)
        else:
            print(error)
        
    def get_project_author_count(self, dir_name: str) -> int:
        p1 = subprocess.Popen(
            ["git", "shortlog", "-sn", "--no-merges"],
            cwd=f"./repositories/{dir_name}",
            stdout=subprocess.PIPE,
            text=True
        )
        p2 = subprocess.Popen(
            ["wc", "-l"],
            cwd=f"./repositories/{dir_name}",
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )

        output, error = p2.communicate()
        if output is not None:
            return int(output)
        else:
            print(error)
        
    def get_num_source_files(self, dir_name: str) -> int:
        p1 = subprocess.Popen(
            ["find", ".", "-iname", "*.java", "-not", "-path", "*/.*"],
            cwd=f"./repositories/{dir_name}",
            stdout=subprocess.PIPE,
            text=True
        )
        p2 = subprocess.Popen(
            ["wc", "-l"],
            cwd=f"./repositories/{dir_name}",
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )

        output, error = p2.communicate()
        if output is not None:
            return int(output)
        else:
            print(error)
    
    def get_source_loc(self, dir_name: str) -> int:
        #find . -iname '*.java' | xargs cat | wc -l
        p1 = subprocess.Popen(
            ["find", ".", "-iname", "*.java"],
            cwd=f"./repositories/{dir_name}",
            stdout=subprocess.PIPE,
            text=True
        )
        p2 = subprocess.Popen(
            ["xargs", "cat"],
            cwd=f"./repositories/{dir_name}",
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )
        p3 = subprocess.Popen(
            ["wc", "-l"],
            cwd=f"./repositories/{dir_name}",
            stdin=p2.stdout,
            stdout=subprocess.PIPE,
            text=True
        )

        output, error = p3.communicate()
        if output is not None:
            return int(output)
        else:
            print(error)
    
    def get_first_commit_date(self, dir_name: str) -> str:
        # git log --pretty=format:'%ad' | tail -1
        p1 = subprocess.Popen(
            ["git", "log", "--pretty=format:'%ad'"],
            cwd=f"./repositories/{dir_name}",
            stdout=subprocess.PIPE,
            text=True
        )
        p2 = subprocess.Popen(
            ["tail", "-1"],
            cwd=f"./repositories/{dir_name}",
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            text=True
        )
        output, error = p2.communicate()
        if output is not None:
            # to format the UTC date into datetime object
            output = output.strip("\'")
            d = datetime.strptime(output, "%a %b %d %X %Y %z")
            return str(d.date())
            #return output
        else:
            print(error)
    
    def remove_repo_directory(self, dir_name: str) -> None:
        shutil.rmtree(f"./repositories/{dir_name}", ignore_errors=True)
    
    def write_data_to_csv(self, repo_name: str, num_revisions: int, num_authors: str, num_source_files: int, num_source_loc: int, first_revision_date: str) -> None:
        with open('csv/ApacheProjectMetrics.csv', 'a') as file:
            writer = csv.writer(file, csv.QUOTE_NONNUMERIC)
            writer.writerow([repo_name, num_revisions, num_authors, num_source_files, num_source_loc, first_revision_date])
    
    def create_csv_file(self) -> None:
        with open('csv/ApacheProjectMetrics.csv', 'w') as file:
            writer = csv.writer(file, csv.QUOTE_NONNUMERIC)
            writer.writerow(['Project Name', 'Number of Revisions', 'Number of Authors', 'Number of Source Files', 'Number of Source LOC', 'Date of First Commit'])
        

if __name__ == '__main__':
    print('Beginning collecting Git data for Apache Java Projects\n')
    metricCollection = ApacheMetricCollection()
    # create empty file
    metricCollection.create_csv_file()

    repos = metricCollection.generate_project_repo_list()
    metricCollection.clone_and_process_gh_repos(repos)
    