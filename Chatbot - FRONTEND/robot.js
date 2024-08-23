const chatBody = document.getElementById('chat-body');
const chatInput = document.getElementById('chat-input');
const chatContainer = document.getElementById('chat-container');
const chatbotIcon = document.getElementById('chatbot-icon');
const stopGeneratingContainer = document.getElementById('stop-generating-container');
const closeIcon = document.getElementById('close-icon');

let generatingResponse = false;

function sendMessage() {
    const userInput = chatInput.value;
    if (userInput.trim() === '') return;

    appendMessage(userInput, 'user-message');
    chatInput.value = '';

    generatingResponse = true;
    stopGeneratingContainer.style.display = 'flex';

    setTimeout(() => {
        if (generatingResponse) {
            getBotResponse(userInput);
            generatingResponse = false;
            stopGeneratingContainer.style.display = 'none';
        }
    }, 2000); //   
}

function stopGeneratingResponse() {
    generatingResponse = false;
    stopGeneratingContainer.style.display = 'none';
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function appendMessage(message, className) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', className);

    function typeMessage(messageElement, message) {
        const speed = 50; // Velocidad de escritura en milisegundos por carácter
        let i = 0;

        function typeWriter() {
            if (i < message.length) {
                messageElement.innerHTML += message.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            }
        }

        typeWriter();
    }

    if (className === 'bot-message') {
        messageElement.style.opacity = '0';
        messageElement.style.transition = 'opacity 0.3s ease-in-out';

        setTimeout(() => {
            messageElement.style.opacity = '1';
            typeMessage(messageElement, message);
        }, 100);
    } else {
        messageElement.innerText = message;
    }

    chatBody.appendChild(messageElement);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function getBotResponse(userInput) {
    let botMessage = '';

    fetch('http://localhost:5000/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ userInput })

    })
    .then(response => response.json())
    .then(data => {
        botMessage = data.respuesta;
        appendMessage(botMessage, 'bot-message');
    })

    
}

function toggleChatbot() {
    if (chatContainer.style.display === 'none') {
        chatContainer.classList.remove('close');
        chatContainer.classList.add('open');
        chatContainer.style.display = 'flex';
    } else {
        chatContainer.classList.remove('open');
        chatContainer.classList.add('close');
        setTimeout(() => {
            chatContainer.style.display = 'none';
        }, 500); // Duración de la animación de cierre
    }
}

function startVoiceRecognition() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendMessage();
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
    };
}