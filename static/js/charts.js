// $(document).ready(function () {
//     //GaugeMeter
//     $('.GaugeMeter').gaugeMeter();
// });

// // Line Bar Green

// const xValues_line = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150];
// const yValues_line = [7, 8, 8, 9, 9, 9, 10, 11, 14, 14, 15];

// new Chart("myChart", {
//     type: "line",
//     data: {
//         labels: xValues_line,
//         datasets: [{
//             fill: false,
//             lineTension: 0,
//             backgroundColor: "red",
//             borderColor: "green",
//             data: yValues_line
//         }]
//     },
//     options: {
//         legend: { display: false },
//         scales: {
//             yAxes: [{ ticks: { min: 6, max: 16 } }],
//         }
//     }
// });

// Stack Bar

// var myContext = document.getElementById("stackedChartID").getContext('2d');

// var myChart = new Chart(myContext, {
//     type: 'bar',
//     data: {
//         labels: ["January", "February", "March",
//             "April", "May", "June", "July",],
//         datasets: [{
//             label: 'Excellent',
//             backgroundColor: "orange",
//             data: [21, 19, 24, 20, 15, 17, 22],
//             stack: 'Stack 0',
//         }, {
//             label: 'Bad performance',
//             backgroundColor: "#61bdfa",
//             data: [2, 1, 3, 4, 1, 5, 4],
//             stack: 'Stack 1' // For multiple stacking 
//         }],
//     },
//     options: {
//         plugins: {
//             title: {
//                 display: true,
//                 text: 'Chart.js Bar Chart - Stacked'
//             },
//         },
//         interaction: {
//             intersect: false,
//         },
//         scales: {
//             x: {
//                 stacked: true,
//             },
//             y: {
//                 stacked: true
//             }
//         },
//         responsive: true
//     }
// });
// Combo charts
// var ctx = document.getElementById('comboChart2').getContext('2d');
// var comboChart = new Chart(ctx, {
//     type: 'bar', // Set the initial type to bar
//     data: {
//         labels: ['January', 'February', 'March', 'April', 'May'],
//         datasets: [
//             {
//                 label: 'Bar Dataset',
//                 backgroundColor: 'rgba(75, 192, 192, 0.2)',
//                 borderColor: 'rgba(75, 192, 192, 1)',
//                 borderWidth: 1,
//                 data: [65, 59, 80, 81, 56]
//             },
//             {
//                 label: 'Line Dataset',
//                 type: 'line',
//                 borderColor: 'rgba(255, 99, 132, 1)',
//                 borderWidth: 2,
//                 fill: false,
//                 data: [28, 48, 40, 19, 86]
//             }
//         ]
//     },
//     options: {
//         scales: {
//             y: {
//                 beginAtZero: true
//             }
//         }
//     }
// });

//  const xValues_line = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150];
//  const yValues_line = [7, 8, 8, 9, 9, 9, 10, 11, 14, 14, 15];

// new Chart("", {
//     type: "line",
//     data: {
//         labels: xValues_line,
//         datasets: [{
//             fill: false,
//             lineTension: 0,
//             backgroundColor: "rgba(0,0,255,1.0)",
//             borderColor: "rgba(0,0,255,0.1)",
//             data: yValues_line
//         }]
//     },
//     options: {
//         legend: { display: false },
//         scales: {
//             yAxes: [{ ticks: { min: 6, max: 16 } }],
//         }
//     }
// });



// PIE
// var xValues_doughnut = ["Italy", "France", "Spain", "USA"];
// var yValues_doughnut = [55, 49, 44, 24];
// var barColors = [
//     "#b91d47",
//     "#00aba9",
//     "#2b5797",
//     "#e8c3b9",
// ];

// new Chart("doughnut", {
//     type: "doughnut",
//     data: {
//         labels: xValues_doughnut,
//         datasets: [{
//             backgroundColor: barColors,
//             data: yValues_doughnut
//         }]
//     },
//     options: {
//         title: {
//             display: true,
//             text: "World Wide Wine Production 2018"
//         }
//     }
// });