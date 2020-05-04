var ssi = require('ssi');

var inputDirectory = "ehp-web-hrs-amir-test/";
var outputDirectory = "data_B/web_output/";
var matcher = "/**/*.shtml";

var includes = new ssi(inputDirectory, outputDirectory, matcher, true);
includes.compile();
