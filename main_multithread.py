#  Mood Board Gen (v1.1)
#    ___      _____     _
#   / _ \ _ _|_   _|_ _| | _____
#  | | | | '_ \| |/ _` | |/ / _ \
#  | |_| | | | | | (_| |   <  __/
#   \___/|_| |_|_|\__,_|_|\_\___|
#
#  Copyright 2022 Louis Dalibard

from PIL import Image, ImageDraw
from os import listdir
from os.path import isfile, join
import math
import random
from colorthief import ColorThief
import colorsys
from tqdm import tqdm
import time
import sys
from threading import Thread

title = "Koe no Katachi"
inputFolder = "../Koe no Katachi/"


rowCount = 6
rowHeight = 720 #Pixels
margin = 30
paletteSize = 30
paletteCount = 5
paletteBorderThickness = 0
paletteRadius = 2

ratios = []
domColor = []
hsvDomColorList = []
hDomColorList = []
paletteList = []


files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f))]
listOfFiles = list(range(len(files)))



processStartTime = time.time()

def paletteGenThread(threadName, file):
    currentImage = Image.open(inputFolder+file)
    color_thief = ColorThief(inputFolder+file)
    rgbDomColor = color_thief.get_color(quality=1)
    hsvDomColor = colorsys.rgb_to_hsv(float(rgbDomColor[0])/255,float(rgbDomColor[1])/255,float(rgbDomColor[2])/255)
    return(threadName,(float(currentImage.size[0])/float(currentImage.size[1])),(rgbDomColor),hsvDomColor,hsvDomColor[0],(color_thief.get_palette(color_count=paletteCount)))

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)

        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        Thread.join(self)
        return self._return

print("Generating palette for:")
threads = []
threadNumber=0
for fileF in files:
    threads.append(ThreadWithReturnValue(target=paletteGenThread, args=(threadNumber,fileF,)))
    threads[threadNumber].start()
    threadNumber+=1

threadNumber=0
for fileF in files:
    print("Waiting...",threadNumber,"/",len(files))
    currentValues = threads[threadNumber].join()
    ratios.append(currentValues[1])
    domColor.append(currentValues[2])
    hsvDomColorList.append(currentValues[3])
    hDomColorList.append(currentValues[4])
    paletteList.append(currentValues[5])
    threadNumber+=1
print("Done.")
print("Sorting images...",end=" ")
zipped_lists = zip(hDomColorList, listOfFiles)
sorted_zipped_lists = sorted(zipped_lists)

sortedByHSV = [element for _, element in sorted_zipped_lists]
print("Done.")
print("Generating layout...",end=" ")
finalComposition = []

for x in range(rowCount):
    finalComposition.append({"headPosition":0,"files":[]})

ComposingFileIndex=0
while (ComposingFileIndex<=len(files)-1):
    minimalHeadPosition=sys.maxsize
    minimalHeadPositionRow=0
    for x in range(rowCount):
        if finalComposition[x]["headPosition"] < minimalHeadPosition:
            minimalHeadPosition = finalComposition[x]["headPosition"]
            minimalHeadPositionRow = x
    currentSelectedImage = sortedByHSV[ComposingFileIndex]
    finalComposition[minimalHeadPositionRow]["files"].append(currentSelectedImage)
    calculatedheadPosition= finalComposition[minimalHeadPositionRow]["headPosition"]+margin+ratios[currentSelectedImage]*rowHeight
    finalComposition[minimalHeadPositionRow]["headPosition"]=calculatedheadPosition
    ComposingFileIndex+=1

maxHeadPosition = 0
for x in range(rowCount):
    if maxHeadPosition < (finalComposition[x]["headPosition"]+60):
        maxHeadPosition=finalComposition[x]["headPosition"]+60

print("Done.")
# Render

finalRenderOutputSize = (int(round(maxHeadPosition)),int(round(rowCount*rowHeight+margin*rowCount*2+rowCount*paletteSize+margin)))
finalRenderOutput = Image.new("RGB",finalRenderOutputSize)
finalRenderOutputLoad = finalRenderOutput.load()
finalRenderOutputDrawContext  = ImageDraw.Draw(finalRenderOutput)

maxDistance = math.sqrt(finalRenderOutputSize[0]**2+finalRenderOutputSize[1]**2)
colorsToInterpol = [hsvDomColorList[sortedByHSV[0]],hsvDomColorList[sortedByHSV[-1]]]
print("Building background gradient...",end=" ")
for i in tqdm(range(finalRenderOutputSize[0])):
    for j in range(finalRenderOutputSize[1]):
        distance = math.sqrt(i**2+j**2)
        gradientProgress = distance/maxDistance
        gradientPixelColor = (colorsToInterpol[1][0]*gradientProgress+colorsToInterpol[0][0]*(1-gradientProgress),colorsToInterpol[1][1]*gradientProgress+colorsToInterpol[0][1]*(1-gradientProgress),colorsToInterpol[1][2]*gradientProgress+colorsToInterpol[0][2]*(1-gradientProgress))
        gradientPixelColorRGB = colorsys.hsv_to_rgb(gradientPixelColor[0],gradientPixelColor[1],gradientPixelColor[2])
        finalRenderOutputLoad[i,j]=(int(round(gradientPixelColorRGB[0]*255)),int(round(gradientPixelColorRGB[1]*255)),int(round(gradientPixelColorRGB[2]*255)))
print("Done.")
print("Building final image...",end="")
for x in range(rowCount):
    headPosition = margin
    for y in range(len(finalComposition[x]["files"])):
        currentImageToPaste = Image.open(inputFolder+files[finalComposition[x]["files"][y]])
        currentRatio = ratios[finalComposition[x]["files"][y]]
        pastePosition = (headPosition, x*rowHeight+margin*x*2+x*paletteSize+margin)
        currentImageToPasteResized = currentImageToPaste.resize((int(round(currentRatio*rowHeight)),int(round(rowHeight))), Image.ANTIALIAS)
        finalRenderOutput.paste(currentImageToPasteResized, pastePosition)
        for j in range(paletteCount):
            paletteTopLeft = (headPosition+j*margin+j*paletteSize,pastePosition[1]+margin+rowHeight)
            paletteBottomRight = (headPosition+j*margin+j*paletteSize+paletteSize,pastePosition[1]+margin+rowHeight+paletteSize)
            paletteColor = paletteList[finalComposition[x]["files"][y]][j]
            paletteColorInverted = (255-paletteColor[0],255-paletteColor[1],255-paletteColor[2])
            finalRenderOutputDrawContext.rounded_rectangle((paletteTopLeft,paletteBottomRight), fill=paletteColor, outline=paletteColorInverted, width=paletteBorderThickness, radius=paletteRadius)
        headPosition+=currentImageToPasteResized.size[0]+margin
    
print("Done.")
print("Saving...",end=" ")
finalRenderOutput.save(title+".moodboard.png")
print("Done.")
