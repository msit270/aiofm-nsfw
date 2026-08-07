---
license: agpl-3.0
tags:
- pytorch
- YOLOv8
- art
- Ultralytics
base_model:
- Ultralytics/YOLO11
- Ultralytics/YOLOv8
library_name: ultralytics
pipeline_tag: object-detection
metrics:
- mAP50
- mAP50-95
---
# Description
YOLOs in this repo are trained with datasets that i have annotated myself, or with the help of my friends(They will be appropriately mentioned in those cases). YOLOs on open datasets will have their own pages.

## Known Adetailer Issues
~~Ultralytics 8.3.217 updates mask handling, which breaks function in main Adetailer repo. Install Ultralytics==8.3.216 or lower. Alternatively - use forks that fix this.~~ - Fixed in main repo.
## My Adetailer fork
I've added some features to make Adetailer more usable and less manual - https://github.com/Anzhc/aadetailer-reforge

#### Want to request a model?
Im open to commissions, hit me up in Discord - **anzhc**

> ## **Table of Contents**
> - [**Face segmentation**](#face-segmentation)
>   - [*Universal*](#universal)
>   - [*Real Face, gendered*](#real-face-gendered)
> - [**Eyes segmentation**](#eyes-segmentation)
> - [**Head+Hair segmentation**](#headhair-segmentation)
> - [**Breasts**](#breasts)
>   - [*Breasts Segmentation*](#breasts-segmentation)
>   - [*Breast size detection/classification*](#breast-size-detection-and-classification)
> - [**Drone detection**](#drone-detection)
> - [**Anime Art Scoring**](#anime-art-scoring)
> - [**Support**](#support)

P.S. All model names in tables have download links attached :3
## Available Models  
### Face segmentation:  
#### Universal:
Series of models aiming at detecting and segmenting face accurately. Trained on closed dataset i annotated myself.
| Model                                                                      | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
|----------------------------------------------------------------------------|-----------------------|--------------------------------|---------------------------|---------------|------------|-------------------|
| [Anzhc Face -seg.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20-seg.pt)         | Face: illustration, real   | LOST DATA               | LOST DATA             |2(male, female)|LOST DATA| 640|
| [Anzhc Face seg 640 v2 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20seg%20640%20v2%20y8n.pt)   | Face: illustration, real   |0.464(box) 0.453(mask)  | 0.309(box) 0.207(mask)|1(face)        |~500| 640|
| [Anzhc Face seg 768 v2 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20seg%20768%20v2%20y8n.pt)   | Face: illustration, real   | ^    | ^ |1(face)        |~500| 768|
| [Anzhc Face seg 768MS v2 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20seg%20768MS%20v2%20y8n.pt) | Face: illustration, real   | ^  | ^ |1(face)        |~500| 768|(Multi-scale)|
| [Anzhc Face seg 1024 v2 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20seg%201024%20v2%20y8n.pt)  | Face: illustration, real   | ^  | ^|1(face)        |~500| 1024|
| [Anzhc Face seg 640 v3 y11n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Face%20seg%20640%20v3%20y11n.pt)  | Face: illustration   | 0.524(box) 0.516(mask)  | 0.387(box) 0.297(mask)|1(face)        |~660| 640|
| [Anzhc Face seg 640 v4 y11n.pt]()  | Face: illustration, real   | 0.835(box) 0.800(mask)  | 0.537(box) 0.467(mask)|1(face)        |~1030| 640|


UPDATE: v3 model has a bit different face target compared to v2, so stats of v2 models suffer compared to v3 in newer benchmark, especially in mask, while box is +- same.
Dataset for v3 and above is going to be targeting inclusion of eyebrows and full eyelashes, for better adetailer experience without large dillution parameter.

Also starting from v3, im moving to yolo11 models, as they seem to be direct upgrade over v8. v12 did not show significant improvement while requiring 50% more time to train, even with installed Flash Attention, so it's unlikely i will switch to it anytime soon.

UPDATE: V4 - Addition of high complexity data (over 100 instances per image), more simple realistic and AI-generated faces.

Benchmark was performed in 640px.
V2 was condensed to single model, as their differences are marginal.  
Benchmark results were recomputed on new val based on V4 dataset(images previously in val remained in val, so no contamination for previous versions), stats updated accordingly.

![image](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/uKrQV5A4-pJKFjkea8DmM.png)

![hjkhgjkghj](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/tWDl0EzBoQFTUHkcgZRJZ.png)

#### Real Face, gendered:
Trained only on real photos for the most part, so will perform poorly with illustrations, but is gendered, and can be used for male/female detection stack.

| Model                       | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- | ----------------------------- | ------------------------- |---------------|------------|-------------------|
  | [Anzhcs ManFace v02 1024 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20ManFace%20v02%201024%20y8n.pt)     | Face: real   | 0.883(box),0.883(mask)        | 0.778(box), 0.704(mask)   |1(face)        |~340        |1024|
  | [Anzhcs WomanFace v05 1024 y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20WomanFace%20v05%201024%20y8n.pt)   | Face: real   | 0.82(box),0.82(mask)          | 0.713(box), 0.659(mask)   |1(face)        |~600        |1024|

Benchmark was performed in 640px.
![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/W0vhyDYLaXuQnbA1Som8f.png)

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/T5Q_mPJ8Ag6jfkaTpmNlM.png)

### Eyes segmentation:
Was trained for the purpose of inpainting eyes with Adetailer extension, and specializes on detecting anime eyes, particularly - sclera area, without adding eyelashes and outer eye area to detection.
Current benchmark is likely inaccurate (but it is all i have), due to data being re-scrambled multi times (dataset expansion for future versions).

| Model                       | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- | ----------------------------- | ------------------------- |---------------|------------|-------------------|
  | [Anzhc Eyes -seg-hd.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Eyes%20-seg-hd.pt)     | Eyes: illustration   | 0.925(box),0.868(mask)        | 0.721(box), 0.511(mask)   |1(eye)        |~500(?)       |1024|


![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/o3zjKGjbXsx0NyB5PNJfM.png)


![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/WIPhP4STirM62b1qBUJWf.png)

### Head+Hair segmentation:
An old model (one of my first). Detects head + hair. Can be useful in likeness inpaint pipelines that need to be automated.

| Model                       | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- | ----------------------------- | ------------------------- |---------------|------------|-------------------|
  | [Anzhc HeadHair seg y8n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20HeadHair%20seg%20y8n.pt)   | Head: illustration, real   | 0.775(box),0.777(mask)        | 0.576(box), 0.552(mask)   |1(head)        |~3180        |640|
  | [Anzhc HeadHair seg y8m.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20HeadHair%20seg%20y8m.pt)   | Head: illustration, real   | 0.867(box),0.862(mask)          | 0.674(box), 0.626(mask)   |1(head)        |~3180        |640|

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/Ic2n8gU4Kcod0XwQ9jzw8.png)

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/oHm-Z5cOPsi7OfhmMEpZB.png)
### Breasts:
#### Breasts segmentation:
Model for segmenting breasts. Was trained on anime images only, therefore has very weak realistic performance, but still is possible.

| Model                       | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- | ----------------------------- | ------------------------- |---------------|------------|-------------------|
  | [Anzhc Breasts Seg v1 1024n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Breasts%20Seg%20v1%201024n.pt)   | Breasts: illustration   | 0.742(box),0.73(mask)        | 0.563(box), 0.535(mask)   |1(breasts)        |~2000        |1024|
  | [Anzhc Breasts Seg v1 1024s.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Breasts%20Seg%20v1%201024s.pt)   | Breasts: illustration   | 0.768(box),0.763(mask)          | 0.596(box), 0.575(mask)   |1(breasts)        |~2000       |1024|
  | [Anzhc Breasts Seg v1 1024m.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhc%20Breasts%20Seg%20v1%201024m.pt)   | Breasts: illustration   | 0.782(box),0.775(mask)          | 0.644(box), 0.614(mask)   |1(breasts)        |~2000       |1024|

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/RoYVk1IgYH1ICiGQrMx6H.png)

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/-QVv21yT6Z4r16M4RvFyS.png)

#### Breast size detection and classification:
Model for Detecting and classifying breast size. Can be used for tagging and moderating content.
Utilizes custom scale, combining default Booru sizes with quite freeform upper range of scale from rule34, simplifying and standartizing it.  

Size range is established relative to body proportion, instead of relative to scene, to not be confused in cases of gigantism and be disentangled from scene.  
And of course it's subjective, since i was the only one annotating data.

| Model                       | Target                |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- |---------------|------------|-------------------|
  | [Anzhcs Breast Size det cls v8 y11m.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20Breast%20size%20det%20cls%20v8%20640%20y11m.pt)| Breasts: illustration and real |15(size range)|~16100        |640|

mAPs are not displayed in table, because i think we need more complex stats for this model.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/5SxX-NqrWrcMQnvBzDQMd.png)

Accurate ratio - correct predictions, exactly matching val.  
+1, -1, +-1 ratio - expanded range of acceptable predictions, by +,- and +-1 class. I suggest using this stat as main accuracy, because +-1 range is likely an acceptable margin of error.  
At annotation, usual rate of error of original data according to this size scale was in range of +-2 to +-3 in some cases, so +-1 should be quite good.  
Miscalss ratio - Correct detection, but classification goes beyond +-1 error.  
Miss ratio - Not seen by model, completely missed.  
False-Positive ratio - Detection of something that isn't there.  
In case of this model i suspect that FPR is also including confusion rate. In some cases multiple detection will be made for single instance, and only 1 will be accepted.  
That can be counted as false-positive, while it will be covered in +-1 acc. Actual FPR should be lower than reported, as tested manually.  
GT Instances - amount of instances of data per class in dataset.  

With that established,  
v8 provides pretty decent quality detection and classification, except for extremes of class 11+, and class 0(flat chest), well, since it's not too simple to detect what's not there.  
Class 2(medium) is one of the most confusing in this case, and has lowest accuracy. From charts, it's mostly mistaken with class 1.  
Rest of classes with reasonable amount of data perform quite well, and achieve high 70s to mid 80s for normal sizes, and up to high 90s for bigger size range.  
Misclassification is quite rare, and im happy with model performance in that regard. Average rate of misclassification is just ~3%.  
Missing predictions is unfortunately over 10%, but data is highly skewed with classes 0-2, which are hard to detect.  
FPR for v8 is very reasonable, assuming confused detections(of 2 classes at once) are counted as FPR. Size range is smooth, and lots of cases where both classes could be applied.  

Last class(unmeasurable) is used for classifying outliers that are hard to measure in currently visible area(e.g. mostly out of frame), but model will try to reasonably predict obstructed and partially visible instances.

All ratios are calculated relative to their respective GT instance count.  

I will continue to use this benchmark approach for future detection models.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/jy0XOcDVNcYlVSyK7FCT3.png)

### Drone detection
Model for segmenting and detecting drones. What a wild swing after entry for breast model, huh. I don't really know, just had an idea, made it work, here we are.

**I would highly advice against using it in anything serious.**

Starting from v03. Consider it as v1, since v03 is my internal iteration.

HIGHLY SENSITIVE TO DRONE MODELS - will have hard time detecting certain types, especially close-up.
Performs poorly on cluttered background.


| Model                       | Target                | mAP 50                        | mAP 50-95                 |Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- | ----------------------------- | ------------------------- |---------------|------------|-------------------|
  | [Anzhcs Drones v03 1024 y11n.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20Drones%20v03%201024%20y11n.pt)   | Drones   | 0.927(box) 0.888(mask)        | 0.753(box) 0.508(mask)   |1(drone)        |~3460        |1024|


![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/Bbjdi0PBDNXmDMhnYBRzb.png)


![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/9UJJdjJ34avY5MmNDVKjS.png)

## Anime Art Scoring
A classification model trained to assign a percentile group based on human preference, instead of trying to directly assign a "quality" label.  
Dataset was composed of about 100k images aged from 1 to 2 years on Danbooru (newer and older images were not used). That limits data to images that were sufficiently viewed and rated, while not being overly exposed due to age, nor underexposed.  
Scores were used and split into percentile groups, each 10%.  

Main interest in making this one was to find out if there is a significant discoverable correlation between scores and image quality.  
Here are my custom charts:  

![image/png](https://cdn-uploads.huggingface.co/production/uploads/633b43d29fe04b13f46c8988/CYJOjJUp-pVhVUCYSDyhb.png)

(top100 is second class due to alphabetical sorting, but for margin acceptance chart it was re-sorted)  

From this chart, considering there are 10 classes in total, i found weak-to-modest correlation between scores and upper half of chart, negative correlation with middle-low part, weak for low, and moderate for lowest.  
  
What does that mean?  

It means that there is meaningful correlation between scoring of people relative to features of art in question, but there is no meaningful correlation between art that is scoring neutrally.  
Negative scoring (top80-100) has moderate correlation, which suggests that there are some uniform negative features we can infere.  
Top60 class is very interesting, because it presents no correlation between provided images, even in top-3 accuracy(it performs at near-random selection in that case(10%)).  
That suggests that there is no feature correlation between art being not noticed, at least not the one YOLO was able to find.  

We can reasonably predict art that will end up in top of the chart by human score, but we are not able to predict middle-of-the line art, which would constitute majority of art in real case.  
We can predict low quality based on human preference reasonably well, but far from ideal.  

Margin acceptance charts - A top-1 accuracy, but with margin of class acceptance(1, 2 and 3(starts with -1, then adds +1 and then -2 class)(it/s not +-1-3 as naming suggests))  
This allows us to see how well are classes correlate. If we see significant increase relative to first chart, that means that second best prediction was selected as top-1.  
We can also see extended correlation trend across classes. We once again can see that middle classes have very low correlation and accuracy, suggesting no meaningful features.  
That kinda suggests to me that there is no reason for art that ended up in middle of dataset to be there, and it would end up higher or lower in perfect world.  

Top10-40 correlates very well, and that can be used for human preference detection. Funny note on that: **bigger the breasts - better the score**.  
And i wholeheartedly support that notion.  
NSFW art in general will have higher preference score, well, what an unexpected outcome, amirite? Dataset was composed ~50/50% from Danbooru/Safebooru(safebooru.donmai.us), so it's not due to overrepresentation of NSFW.  
That is also why you should not use scores for quality tagging, but if you are looking for a thing to maintain high compatibility with current anime models - be my guest.  
Correlation between bottom scores(that you'd use for low quality/worst quality) is weaker, so be conservative with that.  

Bigger model and data will likely see more correlation, but from quick test of just running larger variation did not lead me to better performance.  

| Model                       | Target                |Top-1 acc/(w/ margin(1/2/3))|Top-2 acc|Top-3 acc|Classes        |Dataset size|Training Resolution|
| --------------------------- | --------------------- |---------|---------|---------|---------------|------------|-------------------|
  | [Anzhcs Anime Score CLS v1.pt](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20Anime%20Score%20CLS%20v1.pt)| Anime illustration |0.336(0.467/0.645/0.679)|0.566|0.696|10(top10 to top100)|~98000        |224|

Additionally, i will provide a script for tagging your datasets with that, if you want - [Simple Utility Scripts repo](https://github.com/Anzhc/Simple-Utility-Scripts-for-YOLO/tree/main)

### Support
If you want to support me, feel free to donate on ko-fi:  
https://ko-fi.com/anzhc

Or send me some BTC:  
bc1qpc5kmxrpqp6x8ykdu6976s4rvsz0utk22h80j9

/--UNDER CONSTRUCTION--/