// ============================================
// routes/soilMoisture.routes.js
// ============================================
import express from "express";
import SoilMoistureModel from "../models/soilMoisture.model.js";

const smRouter = express.Router();

// GET: Lấy dữ liệu theo khoảng thời gian
smRouter.get("/", async (req, res) => {
  try {
    const { location_id, start, end } = req.query;
    
    if (!location_id || !start || !end) {
      return res.status(400).json({ error: "Missing parameters" });
    }

    const data = await SoilMoistureModel.getByDateRange(location_id, start, end);
    
    const avgSurface = data.length > 0 
      ? data.reduce((sum, r) => sum + parseFloat(r.sm_surface || 0), 0) / data.length 
      : 0;

    res.json({
      data,
      statistics: {
        average_surface: avgSurface.toFixed(4),
        average_rootzone: (data.reduce((s, r) => s + parseFloat(r.sm_rootzone || 0), 0) / data.length).toFixed(4),
        classification: SoilMoistureModel.classifySoilMoisture(avgSurface),
        days: data.length
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET: Thống kê theo tháng
smRouter.get("/monthly", async (req, res) => {
  try {
    const { location_id, year } = req.query;
    const data = await SoilMoistureModel.getMonthlyStats(location_id, year);
    
    res.json({
      year: parseInt(year),
      monthly_data: data.map(row => ({
        month: parseInt(row.month),
        avg_surface: parseFloat(row.avg_surface || 0).toFixed(4),
        avg_rootzone: parseFloat(row.avg_rootzone || 0).toFixed(4),
        avg_profile: parseFloat(row.avg_profile || 0).toFixed(4),
        classification: SoilMoistureModel.classifySoilMoisture(parseFloat(row.avg_surface))
      }))
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export { smRouter };