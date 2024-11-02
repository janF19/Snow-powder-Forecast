

const express = require('express');
const path = require('path');
const dotenv = require('dotenv');
const axios = require('axios');
const resortRoutes = require('./routes/resorts');



const cron = require('node-cron');

const { exec } = require('child_process');
const fs = require('fs');

// Initialize the app and configure environment variables
dotenv.config();
const app = express();

// Set up middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));

// View engine setup (optional - for rendering HTML)
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');  // You can also use Pug, Handlebars, etc.

// Serve static files from the 'styles' directory
app.use('/styles', express.static(path.join(__dirname, 'styles')));


// Use resort routes (handles the home route as well)
app.use('/', resortRoutes);  // Home route is now part of resortRoutes





// Start the server
const PORT = process.env.PORT || 3002;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
});


const scriptPath = path.join(__dirname, 'getForecastFull_all_resorts.py')
const dataDir = process.env.DATA_DIR || __dirname;
const jsonPath = path.join(__dirname, 'weather_dataFull_7.json')

if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

function fetchWeatherData() {
    console.log('Starting weather data fetch...');
    console.log('Script path:', scriptPath);
    console.log('JSON output path:', jsonPath);

    const options = {
        timeout: 60000,  // 60 second timeout
        maxBuffer: 1024 * 1024, // 1MB buffer
        cwd: __dirname,
        env: { 
            ...process.env,
            PYTHONPATH: process.env.PYTHONPATH || __dirname
        }
    };
    
    exec(`python ${scriptPath}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`Python script error: ${stderr}`);
            return;
        }

        console.log(`Python script output: ${stdout}`);

        // After running the Python script, you can read the JSON data from the file
        fs.readFile(jsonPath, 'utf8', (err, data) => {
            if (err) {
                console.error(`Error reading weather data: ${err.message}`);
                return;
            }

            const weatherData = JSON.parse(data);
            console.log('Weather data:', weatherData);
            
            
        });
    });
}

// Call this function once a day, or on demand

fetchWeatherData()




cron.schedule('00 00 * * *', () => {
    console.log('Fetching daily weather data...');
    fetchWeatherData();
});