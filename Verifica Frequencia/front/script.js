
const form = document.querySelector('#form');
const resultado = document.querySelector('.resultado');



form.addEventListener('submit', function (e) {
    e.preventDefault();
    const pathInput = document.querySelector('.pathInput').value
    const paginasNaoLerInput = document.querySelector('.paginasNaoLer')
    if (paginasNaoLerInput != null) {
        paginasNaoLerInput = paginasNaoLerInput.value
    } 
    const pathOutput = document.querySelector('.pathOutput').value

    const formData ={
        paginasNaoLer: paginasNaoLerInput,
        pathInput: pathInput,
        pathOutput: pathOutput,
    }

    fetch('  https://f2ab-168-121-201-241.ngrok-free.app/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    }).then(response => response.json())
    .catch(error => {
        console.error('Error:', error);})
    
    
    

})
