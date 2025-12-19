function iniciarReserva() {
    const welcome = document.getElementById('welcome-section');
    const services = document.getElementById('services-section');
    
    welcome.style.display = 'none';
    services.classList.remove('hidden');
    services.classList.add('fade-in');
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}