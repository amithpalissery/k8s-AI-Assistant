document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatLog = document.getElementById('chat-log');

    // Function to add a message to the chat log
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (sender === 'user') {
            messageDiv.classList.add('user-message');
        } else {
            messageDiv.classList.add('assistant-message');
        }
        messageDiv.textContent = text;
        chatLog.appendChild(messageDiv);
        chatLog.scrollTop = chatLog.scrollHeight; // Auto-scroll to the bottom
    }

    // Function to handle sending a message
    async function sendMessage() {
        const question = userInput.value.trim();
        if (question === '') return;

        // Display user's message
        addMessage(question, 'user');
        userInput.value = '';

        try {
            // Call the backend API
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Display the assistant's response
            addMessage(data.response, 'assistant');

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, something went wrong. Please try again.', 'assistant');
        }
    }

    // Event listeners for the send button and Enter key
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Initial welcome message
    addMessage('Hello! I am your Kubernetes AI Assistant. How can I help you today?', 'assistant');
});