# Rebook: various book-scan-processing programs

## Spliting

`spliter.py` contains a system for cropping book into left page and right page.

## Cropping

`batch.py` contains a system for cropping various input formats of collections of images and creating a PDF.

## Dewarping

`dewarp.py` contains implementations of two dewarping algorithms:

* [Kim et al. 2015, Document dewarping via text-line based optimization](http://www.sciencedirect.com/science/article/pii/S003132031500165X)
* [Meng et al. 2011, Metric rectification of curved document images](http://ieeexplore.ieee.org/abstract/document/5975161/)

Focal length is currently assumed to be that of the iPhone 7, because that’s what I have been using to test. Change the f value at the top of this file if using a different camera.

The Kim et al. algorithm seems to actually work (and be fast enough to process large numbers of pages in a reasonable amount of time); you can use it directly or via `batch.py --dewarp`.

## Binarization

`binarize.py` contains a ton of binarization algorithms, which should all have mostly-optimized implementations.

* Niblack binarization
* [Sauvola and Pietikäinen 2000, Adaptive document image binarization](http://www.sciencedirect.com/science/article/pii/S0031320399000552)
* [Kamel and Zhao 1993, Extraction of binary character/graphics images from grayscale document images](http://www.sciencedirect.com/science/article/pii/S016786551200311X)
* [Yang and Yan 2000, An adaptive logical method for binarization of degraded document images](http://www.sciencedirect.com/science/article/pii/S0031320399000941)
* [Lu et al. 2010, Document image binarization using background estimation and stroke edges](https://link.springer.com/article/10.1007%2Fs10032-010-0130-8?LI=true) (background estimation portion incomplete)
* [Su et al. 2013, Robust document image binarization technique for degraded document images](https://link.springer.com/article/10.1007%2Fs10032-010-0130-8?LI=true) (DIBCO 2013 champion)
* [Ntirogiannis et al. 2014, A combined approach for the binarization of handwritten document images](http://www.sciencedirect.com/science/article/pii/S016786551200311X)

The last algorithm is the best I've found on this set of inputs.

## Text Structuring

`block.py` contains some text-structuring stuff. I intended to use this as a replacement for the current text-line detection system, but I haven't been able to get it to work.

* [Koo and Choo 2010, State estimation in a document image and its applciation in text block identification and text line extraction](https://link.springer.com/chapter/10.1007/978-3-642-15552-9_31)

## Super-resolution

`upscale.py` has some (incomplete) routines for single-image superresolution using text as a prior.

* [Lee et al. 2007, Efficient sparse coding algorithms](http://papers.nips.cc/paper/2979-efficient-sparse-coding-algorithms.pdf)
* [Walha et al. 2012, Super-resolution of single text image by sparse representation](http://doi.acm.org/10.1145/2432553.2432558)
* [Liu et al. 2014, Blockwise coordinate descent schemes for sparse representation](http://ieeexplore.ieee.org/document/6854608/)

## Disclaimer

I have not examined the patent status of any of these algorithms. Use at your own risk.

Do not use this program to violate copyright laws in your country.

## License (MIT)

Copyright 2018 Patrick Hulin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Robert

Uiteindelijk heb ik maar besloten alleen die mooie baselines te gebruiken die resulteren uit het aanroepen van rebook dewarp zonder het classificatiemodel van Excerptor ervoor, door een aparte scantailor-parameter mee te geven.
Die baselines werden mooi gegroepeerd op veel of weinig curvature, daar komen met de voorbeeldpagina nu 4 potentiele tekstsuperblokken uit die alszodanig vanuit scantailor deviant te consumeren zullen moeten zijn.

Feitelijk laat ik de rest dus voor wat het is en werk ik met de commando's:

```bash
python scantailor_bridge.py 'book/Scan_20250618 (8)_1L.tif'
python inspect_export.py
vi scantailor_export/textblocks.json
grep -E 'block_id|baseline_id|super|deuk_probability' scantailor_export/textblocks.json
```

Met python3.10

### ScanTailor Deviant Integration

Voor integratie in ScanTailor Deviant C++:

#### 1. Bridge Call in Dewarping Stage
```cpp
// In ScanTailor dewarping initialization (DewarpingView.cpp):
void DewarpingView::initializeFromPython(const QString& imagePath) {
    QString scriptPath = QDir::currentPath() + "/python_bridge/scantailor_bridge.py";
    QString command = QString("python3 %1 '%2'").arg(scriptPath, imagePath);
    
    QProcess pythonProcess;
    pythonProcess.execute(command);
    pythonProcess.waitForFinished();
    
    // Load generated JSON files
    loadDetectedSuperBlocks("scantailor_export/textblocks.json");
}
```

#### 2. JSON Import in MultiBlockDistortionModel
```cpp
// In MultiBlockDistortionModel.cpp:
void MultiBlockDistortionModel::loadDetectedSuperBlocks(const QString& jsonPath) {
    QFile file(jsonPath);
    if (!file.open(QIODevice::ReadOnly)) return;
    
    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    QJsonObject root = doc.object();
    
    // Get geographic super blocks
    QJsonObject superBlocks = root["geographic_super_blocks"].toObject();
    QJsonArray blocks = superBlocks["blocks"].toArray();
    
    for (const QJsonValue& blockValue : blocks) {
        QJsonObject block = blockValue.toObject();
        
        int superBlockId = block["super_block_id"].toInt();
        QJsonArray baselineIds = block["baseline_ids"].toArray();
        
        // Create distortion model for this super block
        createDistortionModelFromBaselines(superBlockId, baselineIds, block);
    }
}
```

#### 3. Initialize Splines from Detected Data
```cpp
void MultiBlockDistortionModel::createDistortionModelFromBaselines(
    int superBlockId, 
    const QJsonArray& baselineIds, 
    const QJsonObject& blockData) {
    
    // Get curvature info
    QJsonObject curvatureInfo = blockData["curvature_info"].toObject();
    bool hasDistortion = curvatureInfo["has_distortion"].toBool();
    QString category = curvatureInfo["category"].toString();
    
    // Create initial splines from detected baselines
    std::vector<QPointF> topSplinePoints;
    std::vector<QPointF> bottomSplinePoints;
    
    // Load spline control points from JSON
    QJsonObject splineParams = getFirstModelSplineParams(baselineIds);
    populateSplinePoints(splineParams, topSplinePoints, bottomSplinePoints);
    
    // Create distortion model
    auto distortionModel = std::make_shared<DistortionModel>();
    distortionModel->setSuperBlockId(superBlockId);
    distortionModel->setTopSpline(Spline(topSplinePoints));
    distortionModel->setBottomSpline(Spline(bottomSplinePoints));
    distortionModel->setNeedsCorrection(hasDistortion);
    distortionModel->setCurvatureCategory(category);
    
    // Add to model list
    m_distortionModels[superBlockId] = distortionModel;
    
    // Initialize UI with super block
    initializeSuperBlockUI(superBlockId, category, baselineIds.size());
}
```

#### 4. User Interface for Super Block Selection
```cpp
// In DewarpingOptionsWidget.cpp:
void DewarpingOptionsWidget::initializeSuperBlockUI(
    int superBlockId, 
    const QString& curvatureCategory,
    int numBaselines) {
    
    QString blockLabel = QString("📍 Tekstblok %1").arg(superBlockId);
    QString statusIcon = curvatureCategory.contains("DISTORTED") ? "⚠️" : "✅";
    QString description = QString("%1 %2 (%3 baselines)")
                         .arg(statusIcon, curvatureCategory, QString::number(numBaselines));
    
    // Create UI elements
    QCheckBox* blockCheckbox = new QCheckBox(blockLabel);
    QLabel* statusLabel = new QLabel(description);
    QPushButton* adjustButton = new QPushButton("Fine-tune baselines");
    
    // Connect signals
    connect(blockCheckbox, &QCheckBox::toggled, 
            [this, superBlockId](bool enabled) {
                toggleSuperBlock(superBlockId, enabled);
            });
            
    connect(adjustButton, &QPushButton::clicked,
            [this, superBlockId]() {
                openBaselineEditor(superBlockId);
            });
    
    // Add to layout
    m_superBlockLayout->addWidget(blockCheckbox);
    m_superBlockLayout->addWidget(statusLabel);
    m_superBlockLayout->addWidget(adjustButton);
}
```

#### 5. Runtime Usage Flow
```cpp
// Typical user workflow:
// 1. Load image → automatic Python bridge call
// 2. User sees 4 super blocks with curvature indicators
// 3. User enables/disables super blocks for correction
// 4. User fine-tunes individual baselines within selected super blocks
// 5. Apply dewarp with custom spline adjustments
```

#### 6. Command Integration
```cpp
// Add menu option or toolbar button:
void MainWindow::onDetectBaselines() {
    QString imagePath = getCurrentImagePath();
    m_dewarpingView->initializeFromPython(imagePath);
    
    statusBar()->showMessage("Python baseline detection completed");
}
```

Deze aanpak geeft users:
- **4 geographic super blocks** (van je voorbeeld)
- **Curvature indicators** (DISTORTED/STRAIGHT)  
- **Individual baseline editing** binnen elk super block
- **Clean Python→C++ bridge** zonder complexe dependencies