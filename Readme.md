# GitHub Osint  

This script retrieves email addresses from GitHub repositories for either a specific user or an entire organization. The program processes each user's repositories and collects commit emails, displaying a table of all unique emails found. It handles rate limits (HTTP status codes 403 and 429) using exponential backoff, and retries up to 3 times with increasing time delays.

## Features
- Process either a GitHub **organization** or a **user**.
- Collect commit emails from all repositories (excluding forks).
- Exponential backoff for rate limits: retries with delays of 5 seconds, 30 seconds, and 3 minutes.
- Skip users/repositories after the maximum retry limit (3 retries).
- Display unique emails found in a pandas DataFrame.

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
