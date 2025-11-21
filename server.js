import express from "express";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Import Routes
import rainfallRoutes from "./routes/rainfall.routes.js";
import temperatureRoutes from "./routes/temperature.routes.js";
import locationRoutes from "./routes/location.routes.js";
import { smRouter } from "./routes/soilMoisture.routes.js";
import { ndviRouter } from "./routes/ndvi.routes.js";
import { tvdiRouter } from "./routes/tvdi.routes.js";
import { dashboardRouter } from "./routes/dashboard.routes.js";

// API Routes
app.use("/api/rainfall", rainfallRoutes);
app.use("/api/temperature", temperatureRoutes);
app.use("/api/locations", locationRoutes);
app.use("/api/soil-moisture", smRouter);
app.use("/api/ndvi", ndviRouter);
app.use("/api/tvdi", tvdiRouter);
app.use("/api/dashboard", dashboardRouter);

// Health check
app.get("/api", (req, res) => {
  res.json({ 
    message: "🌍 Web GIS Climate API",
    version: "2.0.0",
    endpoints: {
      locations: "/api/locations",
      rainfall: "/api/rainfall",
      temperature: "/api/temperature",
      soil_moisture: "/api/soil-moisture",
      ndvi: "/api/ndvi",
      tvdi: "/api/tvdi",
      dashboard: "/api/dashboard/overview"
    }
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: "Something went wrong!", message: err.message });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║           🌍 Web GIS Climate API Server                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:${PORT}                    ║
╠══════════════════════════════════════════════════════════════╣
║  API Endpoints:                                              ║
║  • GET /api/locations                                        ║
║  • GET /api/rainfall?location_id=1&start=...&end=...         ║
║  • GET /api/temperature?location_id=1&start=...&end=...      ║
║  • GET /api/soil-moisture?location_id=1&start=...&end=...    ║
║  • GET /api/ndvi?location_id=1&start=...&end=...             ║
║  • GET /api/tvdi?location_id=1&start=...&end=...             ║
║  • GET /api/dashboard/overview?location_id=1&start=...&end=..║
╚══════════════════════════════════════════════════════════════╝
  `);
});