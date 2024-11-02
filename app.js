

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
const PORT = 3002;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});


const scriptPath = path.join(__dirname, 'getForecastFull_all_resorts.py')
const jsonPath = path.join(__dirname, 'weather_dataFull_7.json')


function fetchWeatherData() {
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