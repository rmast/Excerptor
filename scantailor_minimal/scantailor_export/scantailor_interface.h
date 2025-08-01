#ifndef PYTHON_DETECTION_BRIDGE_H
#define PYTHON_DETECTION_BRIDGE_H

#include <vector>
#include <string>
#include <memory>

namespace dewarping {

struct DetectedBaseline {
    int id;
    std::vector<QPointF> points;
    QRectF bounds;
    double curvature_estimate;
    double confidence;
    bool user_modified = false;
};

struct DetectedTextBlock {
    int block_id;
    std::vector<int> baseline_ids;
    int top_baseline_id;
    int bottom_baseline_id;
    QRectF bounds;
    std::string distortion_type;
    double confidence;
    bool user_modified = false;
    
    // Spline control points
    std::vector<QPointF> top_spline_points;
    std::vector<QPointF> bottom_spline_points;
};

class PythonDetectionBridge {
public:
    static bool loadDetectionResults(const std::string& baseline_file,
                                   const std::string& textblock_file);
    
    static std::vector<DetectedBaseline> getBaselines();
    static std::vector<DetectedTextBlock> getTextBlocks();
    
    // Integration met bestaande ScanTailor classes
    static void populateBaselineDetector(BaselineDetector& detector);
    static void populateMultiBlockModel(MultiBlockDistortionModel& model);
    
private:
    static std::vector<DetectedBaseline> baselines_;
    static std::vector<DetectedTextBlock> textblocks_;
};

} // namespace dewarping

#endif // PYTHON_DETECTION_BRIDGE_H