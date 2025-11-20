import express from "express";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Routes
import rainfallRoutes from "./routes/rainfall.routes.js";
import temperatureRoutes from "./routes/temperature.routes.js";
import locationRoutes from "./routes/location.routes.js";

app.use("/api/rainfall", rainfallRoutes);
app.use("/api/temperature", temperatureRoutes);
app.use("/api/locations", locationRoutes);

// Health check
app.get("/", (req, res) => {
  res.json({ 
    message: "Web GIS API is running",
    version: "1.0.0",
    endpoints: {
      locations: "/api/locations",
      rainfall: "/api/rainfall",
      temperature: "/api/temperature"
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: "Something went wrong!",
    message: err.message 
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server đang chạy tại http://localhost:${PORT}`);
  console.log(`📍 API endpoints:`);
  console.log(`   - GET /api/locations`);
  console.log(`   - GET /api/rainfall?location_id=1&start=2020-01-01&end=2020-12-31`);
  console.log(`   - GET /api/temperature?location_id=1&start=2020-01-01&end=2020-12-31`);
});