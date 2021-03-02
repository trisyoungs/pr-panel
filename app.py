import flask, re, toml
from github import Github
from airium import Airium
from time import gmtime, strftime, sleep

# Parse the configuration file and set some values
config = toml.load('config.toml')
# -- Page autorefresh rate (in seconds)
refreshRate = 300
if 'refreshRate' in config:
    refreshRate = config['refreshRate']
# -- Rate Limit Sleep Timeout
sleepInterval = 1.1
if 'sleepInterval' in config:
    sleepInterval = config['sleepInterval']

# Create our Flask app
app = flask.Flask(__name__)
#app.config["DEBUG"] = True

# Create a Github object with our personal access token
gh = Github(config['token'])

def parsePRData(userRepo, test=False):
    """Get PR data for a specific user/repo"""
    if test:
        return [{'number': 516, 'title': 'Protein force fields', 'draft': True}, {'number': 555, 'title': 'Range splitter', 'draft': False, 'conclusion': 'failure', 'checks': {'QC': ['failure', 'success', 'success']}, 'reviews': {'comments': 4, 'changesRequested': 1}}, {'number': 559, 'title': 'EnumOptions Modernisation', 'draft': False, 'conclusion': 'success', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['success', 'success']}, 'reviews': {'approvals': 1}}, {'number': 560, 'title': 'Simplify WindowFunction class', 'draft': True, 'conclusion': 'success', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['success', 'success']}}]

    # Get the specified repo
    repo = gh.get_repo(userRepo)
    sleep(sleepInterval)

    # Obtain PR info for this repo, and extract the info we want
    pulls = repo.get_pulls(state='open', sort='created', direction='asc', base='develop')
    sleep(sleepInterval)

    # If there are no open PRs, can exit now without appending anything to the list
    if len(list(pulls)) == 0:
        return

    # Extract data from the array
    prInfo = []
    for pr in pulls:
        # Store basic information
        newInfo = {}
        newInfo["number"] = pr.number
        newInfo["title"] = pr.title
        newInfo["draft"] = pr.draft

        # Get checks information, and create a simplified representation to store
        checksInfo = {}
        last_commit = [commit for commit in pr.get_commits()][-1]
        sleep(sleepInterval)
        check_suites = last_commit.get_check_suites()
        sleep(sleepInterval)
        for cs in check_suites:
            # Update the overall state of the PR's check suite(s) here
            # -- If the check suite status is "queued" or "in_progress", then we are still running
            if cs.status == "queued" or cs.status == "in_progress":
                newInfo["status"] = "in_progress"
            elif cs.status == "completed":
                # Take the overall status of the check suite as the result
                newInfo["status"] = cs.conclusion

            # Extract data from individual check runs
            for cr in cs.get_check_runs():
                # Does this check run match any mapping in the stageMap?
                for stage in config['stage']:
                    if not re.match(stage['re'], cr.name):
                        continue

                    # What is the status / result of this stage?
                    if cr.status == "queued" or cr.status == "in_progress":
                        status = cr.status
                    else:
                        status = cr.conclusion

                    # Append this check run to our stage info
                    if stage['name'] in checksInfo:
                        checksInfo[stage['name']].append(status)
                    else:
                        checksInfo[stage['name']] = [ status ]

        # Store check run information in the dict
        if checksInfo:
            newInfo["checks"] = checksInfo

        # Get any reviews for this PR
        reviewInfo = {}
        approvals = 0
        comments = 0
        changesRequested = 0
        reviews = pr.get_reviews()
        sleep(sleepInterval)
        for r in reviews:
            if r.state == "APPROVED":
                approvals += 1
            elif r.state == "COMMENTED":
                comments += 1
            elif r.state == "CHANGES_REQUESTED":
                changesRequested += 1
        if approvals > 0:
            reviewInfo['approvals'] = approvals
        if comments > 0:
            reviewInfo['comments'] = comments
        if changesRequested > 0:
            reviewInfo['changesRequested'] = changesRequested

        # Store review info in the dict
        if reviewInfo:
            newInfo['reviews'] = reviewInfo

        prInfo.append(newInfo)
    return prInfo

def prDataToHTML(prData, page):
    # Start a list for the active PRs in this repo
    with page.body().ul(class_="prList"):

        # Loop over PRs
        for pr in prData:
            # Reset variables
            showStatusChecks = True

            # Start a new list item and grid
            with page.li().div(class_="prGrid"):

                # Header line (PR number, title, status)
                # -- Number
                with page.div(class_="prNumberContainer").div(class_="prNumber"):
                    page(f"#{pr['number']}")

                # -- Title and status labels
                with page.div(class_="prTitle"):
                    with page.div(class_="prTitleText"):
                        page(pr['title'])
                    if pr['draft']:
                        with page.div(class_="prTitleLabelContainer").div(class_="prTitleLabel grayLabel"):
                            page("DRAFT")
                    if "reviews" in pr:
                        if "approvals" in pr['reviews']:
                            with page.div(class_="prTitleLabelContainer").div(class_="prTitleLabel"):
                                page.img(src="static/img/success.svg", class_="prStatusIcon")
                                page(pr['reviews']['approvals'])
                        if "changesRequested" in pr['reviews']:
                            with page.div(class_="prTitleLabelContainer").div(class_="prTitleLabel"):
                                page.img(src="static/img/changes.svg", class_="prStatusIcon")
                                page(pr['reviews']['changesRequested'])
                        if "comments" in pr['reviews']:
                            with page.div(class_="prTitleLabelContainer").div(class_="prTitleLabel"):
                                page.img(src="static/img/comment.svg", class_="prStatusIcon")
                                page(pr['reviews']['comments'])

                # -- Status Icon
                with page.div(class_="prStatusContainer"):
                    if not "status" in pr or pr['status'] == "neutral":
                        page.img(src="static/img/unknown.svg", class_="prStatusIcon")
                    elif pr['status'] == "success":
                        page.img(src="static/img/success.svg", class_="prStatusIcon")
                        showStatusChecks = False
                    elif pr['status'] == "failure":
                        page.img(src="static/img/failure.svg", class_="prStatusIcon")
                    elif pr['status'] == "timed_out":
                        page.img(src="static/img/timed_out.svg", class_="prStatusIcon")
                    else:
                        page.img(src="static/img/unknown.svg", class_="prStatusIcon")

                # Status checks line
                if showStatusChecks:
                    # Add on the first div (empty), and open the next one
                    page.div(class_="checkBlank")
                    with page.div(class_="prChecks"):
                        # Do we have checks to go through?
                        if "checks" in pr:
                            # Loop over checks
                            for check,results in pr["checks"].items():
                                # Add stage indicator
                                with page.div(class_="checkName"):
                                    page(check)

                                # Draw check indicators in sequence
                                for result in results:
                                    with page.div(class_="checkStatusContainer"):
                                        if result == "queued":
                                            page.img(src="static/img/queued.svg", class_="checkIcon")
                                        elif result == "in_progress":
                                            page.img(src="static/img/in_progress.svg", class_="checkIcon")
                                        elif result == "skipped":
                                            page.img(src="static/img/skipped.svg", class_="checkIcon")
                                        elif result == "success":
                                            page.img(src="static/img/success.svg", class_="checkIcon")
                                        elif result == "failure":
                                            page.img(src="static/img/failure.svg", class_="checkIcon")
                                        else:
                                            page.img(src="static/img/unknown.svg", class_="checkIcon")
                        else:
                            with page.div(class_="checkStatus"):
                                page("No checks have been run for this PR.")

@app.route('/', methods=['GET'])
def home():
    # Set some vars
    rate = refreshRate

    # Set up the page
    page = Airium()
    page('<!DOCTYPE html>')
    with page.html():
        with page.head():
            page.title("PR Panel")
            page.link(rel="stylesheet", href='static/css/main.css')
            page.meta(http_equiv="refresh", content="REFRESHRATE")

    # Loop over defined repos
    rr = refreshRate
    for repo in config['repo']:
        # Get PR data for the repo
        prs = []
        failed = False
        try:
            prs = parsePRData(repo['id'])
        except:
            failed = True
            rr = 30

        # Add header
        with page.body().div(class_="repoHeader"):
            page(repo['id'])
            with page.div(class_="repoTimeStamp"):
                if failed:
                    page.img(src="static/img/warning.svg", class_="checkIcon")
                page(strftime("%H:%M", gmtime()))

        if failed:
            with page.body().div(class_="repoMessage"):
                page("Failed to get PR info for this repo. Retrying in 30 seconds...")
        elif len(prs):
            prDataToHTML(prs, page)
        else:
            with page.body().div(class_="repoMessage"):
                page("No open PRs for this repository.")

    # Need to tweak the generated html slightly to:
    # - Change the string "http_equiv" to "http-equiv" - we couldn't do this earlier as the '-' is interpreted as a minus in the key.
    # - Set the actual page refresh time, which depends on the success of retrieving repository data
    html = str(page).replace("http_equiv", "http-equiv")
    html = html.replace("REFRESHRATE", str(rr))

    return html

# Run the app
app.run()
