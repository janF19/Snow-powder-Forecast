const express = require('express');
const { getSnowfallForResorts, getPast14DaySnow, getShortForecast, getHistoryData, calculateHistorySnow, getAllResortsForecast, getCombinedForecast, getAllHistoryData, calculateAllHistory, get14dayForecastCombined} = require('../controllers/resortController');

const router = express.Router();

// Home route - fetch snowfall data when user visits the root '/'
router.get('/', getSnowfallForResorts);

//get all resorts from all countries
router.get('/allResortsCombined', getCombinedForecast);


//lists resorts based on coutries
router.get('/allResortsByCountry', getAllResortsForecast);

//14 day forecast for all countries combined
router.get('/14dayForecastCombined', get14dayForecastCombined);
router.get('/past14daysnow', getPast14DaySnow);


router.get('/allHistory', getAllHistoryData);
router.post('/calculate-history-all', calculateAllHistory)




//router.post('/calculate-history-snowfall', calculateHistorySnow)
//router.get('/history', getHistoryData);
// You can add other routes related to resorts here
// e.g., router.get('/specificRoute', specificControllerFunction);

module.exports = router;