
import re
import csv
from apache_metric_collection import ApacheMetricCollection
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

JIRA_URL = "https://issues.apache.org/jira/issues/?jql=project={}"

class JiraIssueCollection:
    def __init__(self) -> None:
        pass

    def get_num_issues(self, inner_text: str) -> int:
        num_issues = 0
        if not inner_text or inner_text == '':
            return num_issues
        else:
            num_issues = int(re.search(r'(\d)*$', inner_text).group())
            return num_issues

    def make_request_to_jira(self, jql_str: str) -> str:
        url = JIRA_URL.format(jql_str)
        inner_text = ''

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options) as driver:
            driver.get(url)
            spans = driver.find_elements(by=By.XPATH, value="/html/body/div[1]/div[2]/div[1]/main/div/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[1]/div/div[1]/span")
            if len(spans) != 0:
                span = spans[0]
                inner_text = span.text
        
        return inner_text

    def write_data_to_csv(self, file_name: str, project_name: str, num_issues: int) -> None:
        with open('csv/{}'.format(file_name), 'a') as file:
            writer = csv.writer(file, csv.QUOTE_NONNUMERIC)
            writer.writerow([project_name, num_issues])
    
    def create_csv_file(self, file_name: str) -> None:
        with open('csv/{}'.format(file_name), 'w') as file:
            writer = csv.writer(file, csv.QUOTE_NONNUMERIC)
            writer.writerow(['Project Name', 'Total Number of JIRA Issues'])

if __name__ == '__main__':
    metricCollection = ApacheMetricCollection()
    projects = metricCollection.generate_project_repo_list()

    jira_issues = JiraIssueCollection()
    jira_issues.create_csv_file('JiraIssues.csv')
    
    for project in projects:
        project_name = project[0]
        text = jira_issues.make_request_to_jira(project_name)
        num_issues = jira_issues.get_num_issues(text)
        jira_issues.write_data_to_csv('JiraIssues.csv', project_name=project_name, num_issues=num_issues)

    