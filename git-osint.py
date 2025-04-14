import requests
import pandas as pd
import time
import logging
from typing import Optional, Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TextColor:
    """ANSI color codes for terminal text formatting"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def display_logo():
    """Display the two-line logo with Illogical and Git OSINT and a disclaimer"""
    logo = f"""
{TextColor.RED}
  III  L       L        OOO  GGG  III  CCCC  AAAAA  L       -   GGG  III  TTTTT
   I   L       L       O   O G     I   C     A   A  L       -  O   O  I     T  
   I   L       L       O   O G  GG I   C     AAAAA  L       -  O   O  I     T
   I   L       L       O   O G   G I   C     A   A  L       -  O   O  I     T
  III  LLLLL   LLLLL    OOO  GGG  III  CCCC  A   A  LLLLL   -   OOO  III    T
              
{TextColor.END}
{TextColor.YELLOW}
  GGG  III  TTTTT    OOO   SSSS  III  N   N TTTTT
 G        I     T   O   O S        I   NN  N   T  
 G  GG    I     T   O   O  SSS     I   N N N   T
 G   G    I     T   O   O     S    I   N  NN   T
  GGG   III    T    OOO   SSSS   III  N   N   T
              - version 1.1 -
{TextColor.END}
              {TextColor.BOLD}- version 1.1 -{TextColor.END}

{TextColor.RED}
-------------------------------------------------------------
For educational and learning purposes only. 
Use at your own discretion.
{TextColor.END}
    """
    print(logo)
    print(f"{TextColor.BOLD}Created by:{TextColor.END} {TextColor.GREEN}Smith{TextColor.END}\n")

def get_user_input() -> tuple[Optional[str], Optional[str]]:
    """Get and validate user input for organization or user mode"""
    while True:
        choice = input("Process (O)rganization or (U)ser? [O/U]: ").strip().upper()
        if choice in ('O', 'U'):
            target = input(f"Enter {'organization' if choice == 'O' else 'GitHub username'}: ").strip()
            logger.info(f"{'Organization' if choice == 'O' else 'User'} selected: {target}")
            return (target, None) if choice == 'O' else (None, target)
        logger.error("Invalid choice! Please enter O or U")

def handle_rate_limits(response: requests.Response) -> int:
    """Calculate wait time based on rate limit headers"""
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 30))
        reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
        return max(retry_after, reset_time - time.time(), 1)
    return 5

def make_github_request(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Make API request with selective retry logic and rate limit handling"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            if response.status_code in (403, 409):
                logger.info(f"{'No data' if response.status_code == 409 else 'Forbidden'} (status {response.status_code}). Skipping...")
                return None
            logger.warning(f"Request failed ({response.status_code}): {url}")
            wait_time = handle_rate_limits(response)
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            time.sleep(2 ** attempt)
    logger.error(f"Max retries exceeded for {url}")
    return None

def get_org_members(org: str) -> List[str]:
    """Fetch all members of a GitHub organization"""
    logger.info(f"Fetching members for {org}")
    response = make_github_request(f"https://api.github.com/orgs/{org}/members")
    return [member['login'] for member in response.json()] if response else []

def get_user_repos(username: str) -> List[Dict]:
    """Fetch non-fork repositories for a user"""
    logger.info(f"Fetching repositories for {username}")
    response = make_github_request(f"https://api.github.com/users/{username}/repos")
    return [repo for repo in response.json() if not repo['fork']] if response else []

def extract_emails_from_repo(owner: str, repo: str) -> Set[str]:
    """Extract unique emails from repository commits"""
    logger.debug(f"Extracting emails from {owner}/{repo}")
    response = make_github_request(f"https://api.github.com/repos/{owner}/{repo}/commits")
    if not response:
        return set()

    emails = set()
    for commit in response.json():
        try:
            email = commit['commit']['author']['email'].lower()
            if not any(noreply in email for noreply in ['noreply', 'users.noreply']):
                emails.add(email)
        except (KeyError, TypeError):
            continue
    return emails

def limit_repos(repos: List[Dict], max_repos: int = 10) -> List[Dict]:
    """Limit the number of repositories to scan based on user input (called once)"""
    if len(repos) <= max_repos:
        return repos

    print(f"Found {len(repos)} repositories. Would you like to:")
    print(f"1. Scan first {max_repos} repositories")
    print("2. Select custom range")
    print("3. Scan all repositories")

    choice = input("Select option (1/2/3): ").strip()
    if choice == "1":
        return repos[:max_repos]
    if choice == "2":
        try:
            start = int(input(f"Start (1-{len(repos)}): ")) - 1
            end = int(input(f"End ({start + 1}-{len(repos)}): "))
            return repos[max(0, start):min(end, len(repos))]
        except ValueError:
            logger.warning("Invalid range. Using first 10 repos.")
            return repos[:max_repos]
    if choice == "3":
        return repos
    logger.warning("Invalid choice. Using first 10 repos.")
    return repos[:max_repos]

def process_target(org: Optional[str], user: Optional[str]) -> Dict[str, List[str]]:
    """Process organization or user to extract emails"""
    results = {}
    targets = []
    limited_repos = {}

    if org:
        logger.info(f"Processing organization: {org}")
        targets = get_org_members(org)
        if not targets:
            logger.warning(f"No members found in {org}")
            return results
        # Pre-fetch and limit repos for all members to avoid multiple prompts
        for target in targets:
            repos = get_user_repos(target)
            if repos:
                limited_repos[target] = limit_repos(repos)
    else:
        logger.info(f"Processing user: {user}")
        targets = [user]
        repos = get_user_repos(user)
        if repos:
            limited_repos[user] = limit_repos(repos)

    for target in targets:
        logger.info(f"Processing: {target}")
        emails = set()
        repos = limited_repos.get(target, [])

        if not repos:
            logger.info(f"No repositories found for {target}")
            continue

        for repo in repos:
            repo_emails = extract_emails_from_repo(target, repo['name'])
            if repo_emails:
                logger.info(f"Found {len(repo_emails)} email(s) in {repo['name']}")
                emails.update(repo_emails)

        if emails:
            results[target] = sorted(emails)

    return results

def display_results(results: Dict[str, List[str]]) -> None:
    """Display results in a formatted table"""
    if not results:
        logger.warning("No emails found")
        return

    data = [{'Username': username, 'Email': email}
            for username, emails in results.items()
            for email in emails]

    print(f"\n{TextColor.BOLD}Results:{TextColor.END}")
    print(pd.DataFrame(data).to_string(index=False))

def main():
    """Main program execution"""
    display_logo()
    org, user = get_user_input()
    display_results(process_target(org, user))

if __name__ == "__main__":
    main()
