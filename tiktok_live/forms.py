from django import forms
from .models import ChatCommands


class ChatCommandsForm(forms.ModelForm):
    class Meta:
        model = ChatCommands
        fields = [
            # Standard commands
            'help_enabled', 'help_command',
            'get_points_enabled', 'get_points_command',
            'transfer_points_enabled', 'transfer_points_command',
            'spin_enabled', 'spin_command',
            'coin_drop_enabled', 'coin_drop_command',
            # Custom commands
            'custom_commands_enabled', 'custom_commands_command',
            'custom_sub_commands_enabled', 'custom_sub_commands_command',
            'custom_user_commands_enabled', 'custom_user_commands_command',
        ]
        widgets = {
            # Standard commands
            'help_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdHelpEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'help_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdHelp',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'get_points_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdGetPointsEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'get_points_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdGetPoints',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'transfer_points_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdTransferPointsEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'transfer_points_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdTransferPoints',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'spin_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdSpinEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'spin_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdSpin',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'coin_drop_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget dx-state-disabled',
                'id': 'checkboxChatCmdCoinDropEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'aria-disabled': 'true',
                'tabindex': '0'
            }),
            'coin_drop_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdCoinDrop',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            # Custom commands
            'custom_commands_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdCustomCommandsEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'custom_commands_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdCustomCommands',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'custom_sub_commands_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdCustomSubCommandsEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'custom_sub_commands_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdCustomSubCommands',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
            'custom_user_commands_enabled': forms.CheckboxInput(attrs={
                'class': 'optionCheckbox dx-show-invalid-badge dx-checkbox dx-checkbox-checked dx-widget',
                'id': 'checkboxChatCmdCustomUserCommandsEnabled',
                'role': 'checkbox',
                'aria-checked': 'true',
                'tabindex': '0'
            }),
            'custom_user_commands_command': forms.TextInput(attrs={
                'class': 'dx-show-invalid-badge dx-textbox dx-texteditor dx-editor-outlined dx-widget',
                'id': 'textboxChatCmdCustomUserCommands',
                'autocomplete': 'off',
                'spellcheck': 'false',
                'tabindex': '0',
                'role': 'textbox'
            }),
        }