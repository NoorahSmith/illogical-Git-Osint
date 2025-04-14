# illogical-Git-Osint V1.1 
Git Osint to get the email addresses of the users under organization / single user
![image](https://github.com/user-attachments/assets/a13c867a-64d0-4d2e-8021-aae7b377991f)

**Now supports Detailed Logs to find out the repos where the commits are made. useful for blueteamers**
![1](https://github.com/user-attachments/assets/218e81b2-5de7-4754-a1ab-f59bff5c6359)
inspired by Gitrob



This script retrieves email addresses from GitHub repositories for either a specific user or an entire organization. The program processes each user's repositories and collects commit emails, displaying a table of all unique emails found. It handles rate limits (HTTP status codes 403 and 429) using exponential backoff, and retries up to 3 times with increasing time delays.




## Features
- Process either a GitHub **organization** or a **user**.
- Collect commit emails from all repositories (excluding forks).
- Exponential backoff for rate limits: retries with delays of 5 seconds, 30 seconds, and 3 minutes.
- Skip users/repositories after the maximum retry limit (3 retries).
- Display unique emails found in a pandas DataFrame.
- Ask the user if github account / organization has more than 10 repos since no rate limiting has been implemented .
**GHP Token Authentication** (Work in Progress): The feature to authenticate using a GitHub Personal Access Token (GHP Token) is under development. This will help to avoid hitting rate limits and provide more secure access.
- **Proxy Chains Support** (Work in Progress): The functionality to run the script behind a proxy using `proxychains` or `proxychains-ng` is under development. This will allow for anonymity or the bypassing of geo-restrictions.
- **Multithread Support** (Work in Progress): Multithreading is being added to speed up the processing of repositories. This will allow for concurrent handling of multiple repositories, improving performance.
![3](https://github.com/user-attachments/assets/4c0a9b94-b99b-4342-9d7f-2e5e1e67ab7d)

## Requirements
Before running the script, make sure you have Python 3 and the required dependencies installed. You can install the required libraries using the `requirements.txt` file.

### Prerequisites
- Python 3.x
- Libraries listed in `requirements.txt`

## Installation

1. Clone the repository or download the script file.
2. Install the required dependencies from `requirements.txt`:

   ```bash
   pip3 install -r requirements.txt
