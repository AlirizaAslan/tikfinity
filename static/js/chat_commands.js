// Chat Commands JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Function to handle checkbox changes
    const checkboxes = document.querySelectorAll('.optionCheckbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const commandType = this.id.replace('checkboxChatCmd', '').replace('Enabled', '').toLowerCase();
            const commandText = this.closest('.dx-field').querySelector('input[type="text"]').value;
            
            updateCommandSetting(commandType, this.checked, commandText);
        });
    });
    
    // Function to handle text input changes
    const textInputs = document.querySelectorAll('.dx-texteditor-input');
    textInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fieldDiv = this.closest('.dx-field');
            const checkbox = fieldDiv.querySelector('.optionCheckbox');
            const commandType = checkbox.id.replace('checkboxChatCmd', '').replace('Enabled', '').toLowerCase();
            
            updateCommandSetting(commandType, checkbox.checked, this.value);
        });
    });
    
    // Function to update command setting via AJAX
    function updateCommandSetting(commandType, enabled, commandText) {
        fetch('/tiktok_live/update_chat_command/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: `command_type=${commandType}&enabled=${enabled}&command_text=${commandText}`
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                console.log(`Command ${commandType} updated successfully`);
                showNotification('Command settings saved successfully!', 'success');
            } else {
                console.error('Failed to update command setting');
                showNotification('Failed to save command settings', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error saving command settings', 'error');
        });
    }
    
    // Utility function to show notifications
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '10px 20px',
            borderRadius: '4px',
            color: 'white',
            zIndex: '10000',
            fontWeight: 'bold'
        });
        
        if (type === 'success') {
            notification.style.backgroundColor = '#28a745';
        } else {
            notification.style.backgroundColor = '#dc3545';
        }
        
        // Add to document and auto-remove after 3 seconds
        document.body.appendChild(notification);
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }
    
    // Placeholder for navigation and utils functions
    window.navigation = {
        pageChange: function(page) {
            console.log('Navigating to:', page);
            // In a real implementation, this would handle page navigation
        }
    };
    
    window.utils = {
        openHelpPopup: function(element) {
            const helpDiv = element.parentNode.nextElementSibling;
            if (helpDiv && helpDiv.querySelector('.helptitle') && helpDiv.querySelector('.helptext')) {
                const title = helpDiv.querySelector('.helptitle').innerText;
                const text = helpDiv.querySelector('.helptext').innerText;
                
                // Create a modal-like popup
                const popup = document.createElement('div');
                popup.className = 'help-popup';
                popup.innerHTML = `
                    <div class="help-popup-content">
                        <h3>${title}</h3>
                        <p>${text}</p>
                        <button onclick="this.closest('.help-popup').remove()">Close</button>
                    </div>
                `;
                
                Object.assign(popup.style, {
                    position: 'fixed',
                    top: '0',
                    left: '0',
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    zIndex: '9999',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                });
                
                Object.assign(popup.querySelector('.help-popup-content').style, {
                    backgroundColor: 'white',
                    padding: '20px',
                    borderRadius: '8px',
                    maxWidth: '500px',
                    maxHeight: '80vh',
                    overflow: 'auto'
                });
                
                document.body.appendChild(popup);
            }
        }
    };
    
    window.obsoverlays = {
        scrollToWidget: function(widgetId) {
            console.log('Scrolling to widget:', widgetId);
            // In a real implementation, this would scroll to a specific widget
        }
    };
});

// Additional utility functions for the chat commands
const ChatCommandsManager = {
    // Function to validate command syntax
    validateCommand: function(command) {
        // Check if command starts with '!'
        if (!command.startsWith('!')) {
            return false;
        }
        
        // Check if command has valid characters (letters, numbers, underscore, hyphen)
        const commandPattern = /^![a-zA-Z0-9_-]+$/;
        return commandPattern.test(command);
    },
    
    // Function to reset all commands to default values
    resetToDefaults: function() {
        if (confirm('Are you sure you want to reset all commands to default values?')) {
            // Reset all command text inputs to their default values
            document.getElementById('textboxChatCmdHelp').value = '!help';
            document.getElementById('textboxChatCmdGetPoints').value = '!score';
            document.getElementById('textboxChatCmdTransferPoints').value = '!send';
            document.getElementById('textboxChatCmdSpin').value = '!spin';
            document.getElementById('textboxChatCmdCoinDrop').value = '!coindrop';
            document.getElementById('textboxChatCmdCustomCommands').value = '!commands';
            document.getElementById('textboxChatCmdCustomSubCommands').value = '!subcommands';
            document.getElementById('textboxChatCmdCustomUserCommands').value = '!mycommands';
            
            // Reset all checkboxes to checked
            document.getElementById('checkboxChatCmdHelpEnabled').checked = true;
            document.getElementById('checkboxChatCmdGetPointsEnabled').checked = true;
            document.getElementById('checkboxChatCmdTransferPointsEnabled').checked = true;
            document.getElementById('checkboxChatCmdSpinEnabled').checked = true;
            document.getElementById('checkboxChatCmdCoinDropEnabled').checked = true;
            document.getElementById('checkboxChatCmdCustomCommandsEnabled').checked = true;
            document.getElementById('checkboxChatCmdCustomSubCommandsEnabled').checked = true;
            document.getElementById('checkboxChatCmdCustomUserCommandsEnabled').checked = true;
            
            // Save the changes
            document.querySelector('.btn-save').click();
        }
    },
    
    // Function to test if a command is unique across all commands
    isUniqueCommand: function(command, currentElement) {
        const allCommandInputs = document.querySelectorAll('input[type="text"][id^="textboxChatCmd"]');
        for (let input of allCommandInputs) {
            if (input !== currentElement && input.value === command) {
                return false;
            }
        }
        return true;
    }
};

// Add event listeners for real-time validation
document.addEventListener('DOMContentLoaded', function() {
    const commandInputs = document.querySelectorAll('input[type="text"][id^="textboxChatCmd"]');
    
    commandInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const command = this.value.trim();
            
            if (command && !ChatCommandsManager.validateCommand(command)) {
                this.style.borderColor = '#dc3545';
                this.title = 'Command must start with ! and contain only letters, numbers, underscore, or hyphen';
            } else if (command && !ChatCommandsManager.isUniqueCommand(command, this)) {
                this.style.borderColor = '#dc3545';
                this.title = 'This command is already in use by another function';
            } else {
                this.style.borderColor = '#28a745';
                this.title = '';
            }
        });
    });
});