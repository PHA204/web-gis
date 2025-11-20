import express from "express";
import pool from "../config/db.js";

const router = express.Router();

// GET: lấy dữ liệu theo khoảng thời gian
router.get("/", async (req, res) => {
  try {
    const { location_id, start, end } = req.query;
    const result = await pool.query(
      `SELECT date, rainfall_mm FROM rainfall_data
       WHERE location_id=$1 AND date BETWEEN $2 AND $3
       ORDER BY date ASC`,
      [location_id, start, end]
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET: so sánh hai khoảng thời gian cùng khu vực
router.get("/compare-periods", async (req, res) => {
  try {
    const { location_id, start1, end1, start2, end2 } = req.query;

    const p1 = await pool.query(
      `SELECT SUM(rainfall_mm) AS total FROM rainfall_data
       WHERE location_id=$1 AND date BETWEEN $2 AND $3`,
      [location_id, start1, end1]
    );

    const p2 = await pool.query(
      `SELECT SUM(rainfall_mm) AS total FROM rainfall_data
       WHERE location_id=$1 AND date BETWEEN $2 AND $3`,
      [location_id, start2, end2]
    );

    res.json({
      period_1: Number(p1.rows[0].total || 0),
      period_2: Number(p2.rows[0].total || 0),
      difference: Number((p1.rows[0].total || 0) - (p2.rows[0].total || 0))
    });

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET: so sánh hai khu vực cùng thời gian
router.get("/compare-locations", async (req, res) => {
  try {
    const { location1, location2, start, end } = req.query;

    const q = `
      SELECT location_id, SUM(rainfall_mm) AS total
      FROM rainfall_data
      WHERE location_id IN ($1,$2)
      AND date BETWEEN $3 AND $4
      GROUP BY location_id
    `;

    const result = await pool.query(q, [location1, location2, start, end]);
    res.json(result.rows);

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
