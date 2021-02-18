#!/usr/bin/python
from github import Github
from PIL import Image,ImageDraw,ImageFont
import re

# Main GitHubPRPanel class
class GitHubPRPanel:
    def __init__(self, gitHubInstance):
        self.gh = gitHubInstance

    def getPRData(self, userRepo, stageMap):
        """Get PR data for a specific user/repo"""
        repo = None
        try:
            repo = self.gh.get_repo(userRepo)
        except:
            print(f"Couldn't retrieve repo data for '{userRepo}'.\n")
            return

        # Obtain PR info for this repo, and extract the info we want
        pulls = repo.get_pulls(state='open', sort='created', base='develop')

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

            # Get checks information, and create a simplified representation to store
            checksInfo = {}
            last_commit = [commit for commit in pr.get_commits()][-1]
            check_suites = last_commit.get_check_suites()
            for cs in check_suites:
                # Is a general conclusion for the check suite available
                if cs.conclusion and not "conclusion" in newInfo:
                    newInfo["conclusion"] = cs.conclusion;

                # Extract data from individual check runs
                for cr in cs.get_check_runs():
                    # Does this check run match any mapping in the stageMap?
                    for stageName,pattern in stageMap.items():
                        if not re.match(pattern, cr.name):
                            continue

                        # What is the status / result of this stage?
                        if cr.status == "queued" or cr.status == "in_progress":
                            status = cr.status
                        else:
                            status = cr.conclusion

                        # Append this check run to our stage info
                        if stageName in checksInfo:
                            checksInfo[stageName].append(status)
                        else:
                            checksInfo[stageName] = [ status ]
                    
            # Add check run information to the list
            if checksInfo:
                newInfo["checks"] = checksInfo
            prInfo.append(newInfo)

        return prInfo

    def renderFailureIcon(self, imageDrawObject, pos=(0,0), size=10, colour=0, width=2, outerWidth=1):
        unit = size/5
        imageDrawObject.arc((pos[0],pos[1],pos[0]+size, pos[1]+size), 0, 360, width=outerWidth, fill=colour)
        imageDrawObject.line((pos[0]+1.5*unit,pos[1]+1.5*unit,pos[0]+3.5*unit,pos[1]+unit*3.5), width=width, fill=colour)
        imageDrawObject.line((pos[0]+1.5*unit,pos[1]+3.5*unit,pos[0]+3.5*unit,pos[1]+1.5*unit), width=width, fill=colour)
        return
        
    def renderSuccessIcon(self, imageDrawObject, pos=(0,0), size=10, colour=0, width=2, outerWidth=1):
        unit = size/5
        imageDrawObject.arc((pos[0],pos[1],pos[0]+size, pos[1]+size), 0, 360, width=outerWidth, fill=colour)
        imageDrawObject.line((pos[0]+unit,pos[1]+size/2,pos[0]+2*unit,pos[1]+unit*4,pos[0]+4*unit,pos[1]+unit), width=width, fill=colour)
        return

    def renderSkippedIcon(self, imageDrawObject, pos=(0,0), size=10, colour=0, width=2, outerWidth=1):
        imageDrawObject.arc((pos[0],pos[1],pos[0]+size, pos[1]+size), 0, 360, width=outerWidth, fill=colour)
        imageDrawObject.line((pos[0]+1.5*unit,pos[1]+unit,pos[0]+3*unit,pos[1]+unit*2.5,pos[0]+1.5*unit,pos[1]+4*unit), width=width, fill=colour)
        imageDrawObject.line((pos[0]+2.5*unit,pos[1]+unit,pos[0]+4*unit,pos[1]+unit*2.5,pos[0]+2.5*unit,pos[1]+4*unit), width=width, fill=colour)
        unit = size/5
        return

    def renderInProgressIcon(self, imageDrawObject, pos=(0,0), size=10, colour=0, width=2, outerWidth=1):
        unit = size/5
        for n in range(5):
            imageDrawObject.arc((pos[0],pos[1],pos[0]+size, pos[1]+size), n*360/5, n*360/5+45, width=outerWidth, fill=colour)
        imageDrawObject.polygon((pos[0]+2*unit,pos[1]+1.5*unit,pos[0]+3.5*unit,pos[1]+unit*2.5,pos[0]+2*unit,pos[1]+3.5*unit), fill=colour)
        return

    def renderUnknownIcon(self, imageDrawObject, pos=(0,0), size=10, colour=0, width=2, outerWidth=1):
        unit = size/5
        imageDrawObject.arc((pos[0],pos[1],pos[0]+size, pos[1]+size), 0, 360, width=outerWidth, fill=colour)
        return

    def elideText(self, imageDrawObject, text, font, availableWidth):
        # Does the supplied text fit in the available width without modification?
        textSize = imageDrawObject.textsize(text, font)
        if textSize[0] <= availableWidth:
            return text

        # Calculate the size of an ellipsis
        ellipsisSize = imageDrawObject.textsize('...', font)

        # Reduce length of string until it fits in the available width (accounting for the ellipsis)
        reducedText = text[:-1]
        while (imageDrawObject.textsize(reducedText, font)[0] + ellipsisSize[0]) > availableWidth:
            reducedText = reducedText[:-1]
            if len(reducedText) == 0:
                return ""
        return reducedText + '...'

    def renderPRData(self, prData, imageWidth, imageHeight, baseFontSize, margin=2):
        # Instantiate fonts and colours
        font100 = ImageFont.truetype("assets/NotoSans-Regular.ttf", baseFontSize)
        font80 = ImageFont.truetype("assets/NotoSans-Regular.ttf", int(baseFontSize*0.8))
        primaryColour = (0,0,0)
        invertedPrimaryColour = (255,255,255)
        errorColour = (200,0,0)

        # Create a basic image and clear it
        image = Image.new('RGB', (imageWidth, imageHeight), (255,255,255))
        draw = ImageDraw.Draw(image)
        y = margin
        x = margin
        for repoName,prs in prData.items():
            # Draw header
            draw.text((x,y), repoName, fill=primaryColour, font=font100)
            y += draw.textsize(repoName)[1] + 3
            draw.line((x,y,imageWidth-margin,y), fill=fadedColour/2)
            y += 1

            # Draw PRs
            for pr in prs:
                # Reset variables
                x = margin
                renderStatusChecks = True

                # Info line (PR number, title, status)
                # -- PR Number
                text = f"#{pr['number']}"
                textSize = draw.textsize(text, font=font80)
                draw.text((x,y+baseFontSize*0.1), text, fill=errorColour, font=font80)
                x += textSize[0] + 2
                # -- Title (elided to fit)
                titleText = self.elideText(draw, pr['title'], font100, imageWidth - margin - x - baseFontSize)
                textSize = draw.textsize(titleText, font=font100)
                draw.text((x,y), titleText, fill=primaryColour, font=font100)
                if not "conclusion" in pr:
                    self.renderUnknownIcon(draw, pos=(x + textSize[0] + 2,y+2), size=baseFontSize)
                elif pr['conclusion'] == "success":
                    self.renderSuccessIcon(draw, pos=(x + textSize[0] + 2,y+2), size=baseFontSize)
                    renderStatusChecks = False
                elif pr['conclusion'] == "failure":
                    self.renderFailureIcon(draw, pos=(x + textSize[0] + 2,y+2), size=baseFontSize)
                elif pr['conclusion'] == "failure":
                    self.renderInProgressIcon(draw, pos=(x + textSize[0] + 2,y+2), size=baseFontSize)
                y += textSize[1] + 2

                # Status checks - only display if status != success
                if renderStatusChecks:
                    if "checks" in pr:
                        # Calculate some basic metrics
                        stageBlock = [0,0]
                        for check in pr["checks"]:
                            checkSize = draw.textsize(check, font=font80)
                            for n in range(2):
                                if checkSize[n] > stageBlock[n]:
                                    stageBlock[n] = checkSize[n]
                        stageBlock[0] += 2     # One pixel margin
                        stageBlock[1] += 2     # One pixel margin
                        unit = stageBlock[1] / 5;
    
                        for check,results in pr["checks"].items():
                            # Draw stage indicator
                            textSize = draw.textsize(check, font=font80)
                            draw.rectangle((x,y,x+stageBlock[0],y+stageBlock[1]), fill=fadedColour)
                            draw.text((x+1+(stageBlock[0]-2-textSize[0])/2,y+1), check, font=font80, fill=invertedPrimaryColour)
                            x += stageBlock[0] + 2
    
                            # Draw check indicators in sequence
                            for result in results:
                                if result == "queued":
                                    self.renderQueuedIcon(draw, pos=(x,y), size=stageBlock[1])
                                elif result == "in_progress":
                                    self.renderInProgressIcon(draw, pos=(x,y), size=stageBlock[1])
                                elif result == "skipped":
                                    self.renderSkippedIcon(draw, pos=(x,y), size=stageBlock[1])
                                elif result == "success":
                                    self.renderSuccessIcon(draw, pos=(x,y), size=stageBlock[1])
                                elif result == "failure":
                                    self.renderFailureIcon(draw, pos=(x,y), size=stageBlock[1])
                                else:
                                    self.renderUnknownIcon(draw, pos=(x,y), size=stageBlock[1])
                                x += stageBlock[1] + 2
                                
                        # Move down
                        y += baseFontSize*0.8 + 2
                    else:
                        draw.text((x,y), "No checks have been run for this PR.", font=font80, fill=primaryColour/2)
                        y += baseFontSize*0.8 + 2

                # Leave a small gap between PR lines
                y += 2
        return image

