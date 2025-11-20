import express from "express";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

import rainfallRoutes from "./routes/rainfall.routes.js";
app.use("/rainfall", rainfallRoutes);

app.listen(process.env.PORT, () => {
  console.log(`Server đang chạy tại cổng ${process.env.PORT}`);
});
