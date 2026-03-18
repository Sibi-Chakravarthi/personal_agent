const car = document.getElementById('f1-car');

function scrollCar() {
    let currentTop = parseInt(car.style.top);
    if (currentTop < -200 || currentTop > window.innerHeight) {
        currentTop = 0;
    }
    car.style.top = `${currentTop + 2}px`;
}

setInterval(scrollCar, 20);