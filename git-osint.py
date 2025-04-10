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
              - version 1.0 -
{TextColor.END}
{TextColor.YELLOW}
  GGG  III  TTTTT    OOO   SSSS  III  N   N TTTTT
 G        I     T   O   O S        I   NN  N   T  
 G  GG    I     T   O   O  SSS     I   N N N   T
 G   G    I     T   O   O     S    I   N  NN   T
  GGG   III    T    OOO   SSSS   III  N   N   T
              - version 1.0 -
{TextColor.END}
              {TextColor.BOLD}- version 1.0 -{TextColor.END}

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
        if choice == 'O':
            org = input("Enter organization name: ").strip()
            logger.info(f"Organization selected: {org}")
            return org, None
        elif choice == 'U':
            user = input("Enter GitHub username: ").strip()
            logger.info(f"User selected: {user}")
            return None, user
        logger.error("Invalid choice! Please enter O or U")

def handle_rate_limits(response: requests.Response) -> int:
    """Calculate appropriate wait time based on rate limit headers"""
    if response.status_code == 403:
        reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
        return max(reset_time - time.time(), 1)
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 30))
        return retry_after
    return 5  # Default wait time for other errors

def make_github_request(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Make API request with retry logic and rate limit handling"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            
            logger.warning(f"Request failed ({response.status_code}): {url}")
            if 400 <= response.status_code < 500:
                wait_time = handle_rate_limits(response)
                logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            elif response.status_code >= 500:
                # Server error handling
                logger.warning(f"Server error ({response.status_code}). Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                time.sleep(2 ** attempt)  # Exponential backoff
            
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            time.sleep(2 ** attempt)
    
    logger.error(f"Max retries exceeded for {url}")
    return None

def get_org_members(org: str) -> List[str]:
    """Fetch all members of a GitHub organization"""
    logger.info(f"Fetching members for {org}")
    url = f"https://api.github.com/orgs/{org}/members"
    response = make_github_request(url)
    return [member['login'] for member in response.json()] if response else []

def get_user_repos(username: str) -> List[Dict]:
    """Fetch non-fork repositories for a user"""
    logger.info(f"Fetching repositories for {username}")
    url = f"https://api.github.com/users/{username}/repos"
    response = make_github_request(url)
    return [repo for repo in response.json() if not repo['fork']] if response else []

def extract_emails_from_repo(owner: str, repo: str) -> Set[str]:
    """Extract unique emails from repository commits"""
    logger.debug(f"Extracting emails from {owner}/{repo}")
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    response = make_github_request(url)
    
    if not response:
        return set()
    
    emails = set()
    for commit in response.json():
        try:
            email = commit['commit']['author']['email'].lower()
            if not any(noreply in email for noreply in ['noreply', 'users.noreply']):
                emails.add(email)
        except (KeyError, AttributeError):
            continue
    return emails

def limit_repos(repos: List[Dict], max_repos: int = 10) -> List[Dict]:
    """Limit the number of repositories to scan based on user input"""
    if len(repos) > max_repos:
        print(f"The organization/user has more than {max_repos} repositories. Would you like to:")
        print(f"1. Scan the first {max_repos} repositories?")
        print(f"2. Provide a custom range (e.g., 14-30)?")
        print(f"3. Scan all repositories?")
        
        choice = input("Please select an option (1/2/3): ").strip()
        
        if choice == "1":
            repos = repos[:max_repos]
        elif choice == "2":
            start = int(input(f"Enter the starting repository number (1 to {len(repos)}): ").strip())
            end = int(input(f"Enter the ending repository number (start to {len(repos)}): ").strip())
            repos = repos[start-1:end]  # Adjusting for 0-based index
        elif choice == "3":
            pass  # Use all repositories as is
        else:
            print("Invalid choice, proceeding with the default option (first 10 repos).")
            repos = repos[:max_repos]
    
    return repos

def process_target(org: Optional[str], user: Optional[str]) -> Dict[str, List[str]]:
    """Main processing function for organizations or users"""
    results = {}
    targets = []
    
    if org:
        logger.info(f"Processing organization: {org}")
        targets = get_org_members(org)
        if not targets:
            logger.warning(f"No members found in {org}")
            return {}
    elif user:
        logger.info(f"Processing user: {user}")
        targets = [user]
    
    for target in targets:
        logger.info(f"Processing: {target}")
        emails = set()
        repos = get_user_repos(target)
        
        repos = limit_repos(repos)  # Limit repos based on user input
        
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
    
    data = []
    for username, emails in results.items():
        for email in emails:
            data.append({'Username': username, 'Email': email})
    
    df = pd.DataFrame(data)
    print(f"\n{TextColor.BOLD}Results:{TextColor.END}")
    print(df.to_string(index=False))

def main():
    """Main program execution"""
    display_logo()
    org, user = get_user_input()
    results = process_target(org, user)
    display_results(results)

if __name__ == "__main__":
    main()
