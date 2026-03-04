# RPG Chat Client
UI Layout Specification

Version: 1.0


# 1. General Layout

The application uses a vertical layout divided into functional blocks.

Main window layout:

Server Status

Character Setup

Descriptions

Character Goal

World Scenario

Story Direction

Scene Memory

Chat History

Message Input

Controls

Token Monitor

Advanced Options


# 2. Window Size

Default window size:

960 x 900


Minimum size:

820 x 700


The interface must support vertical scrolling.


# 3. Server Status Section

Displays connection status to LM Studio.

Elements:

LM Studio Status Label

Reconnect Button

Memory Limit Field


Example:

LM Studio: Connected

[Reconnect]

Memory Limit: 4096


# 4. Character Setup

Fields:

Player Name

Character Name


Example:

Player Name: Player

Character Name: Character


# 5. Descriptions Section

Three text fields:

Player Description

Character Description

World Scenario


Each field must include help text below it.

Help text example:

Write short lines.
One line = one idea.

Recommended length limits:

Player Description: 4–6 lines
Character Description: 4–6 lines
World Scenario: 6–8 lines

Short lines are preferred.
Long paragraphs should be avoided.


# 6. Character Goal

Multiline text field.

Purpose:

Describe the goals or hidden intentions of the Character.


Example:

Character tries to discover who Player is
Character hides secret about the church


# 7. Story Direction

Multiline text field.

Purpose:

Guide the direction of the story.

Recommended limit:

Maximum 8 lines.

Example:

Character distrusts Player
Atmosphere should be tense
Do not reveal the secret yet

# 8. Scene Memory

Multiline text field.

Purpose:

Store summarized events.

Recommended limit:

Maximum 10 lines.

Example:

Player arrived in abandoned town
Character distrusts Player
Bell rings at midnight


# 9. Chat History

Scrollable text area.

Displays conversation in format:

Player: message

Character: message


Chat history should auto-scroll to the newest message.

Chat history field is read-only.

Reason:

Direct manual edits can break turn consistency used by Redo Response.


# 10. Message Input

Multiline text field for writing new messages.

Below the input field:

Speaker Selector


Options:

Player

Character


# 11. Controls

Buttons:

Send Message

Generate Response

Enhance Message

Redo Response

Make Summary

Delete Last Message

Save Game

Load Game

Stop Generation

Bug fix note:

Delete Last Message is the supported way to adjust recent history
without breaking redo behavior.


# 12. Token Monitor

Displays:

Context tokens used

Maximum tokens

Estimated last output tokens


Example:

Context tokens: 2150 / 4096
Last request: 178 tokens


Color indicators:

Green — safe

Orange — approaching limit

Red — near limit


# 13. Advanced Options

Hidden panel.

Expandable section.

Contains:

Temperature

Top P

Presence Penalty

Frequency Penalty

Max Tokens

Prompt Debug Mode


# 14. Editable Field Shortcuts

All editable text controls must support standard keyboard shortcuts for
clipboard operations.

Required mappings:

- `Ctrl+C` / `Ctrl+Insert` => copy
- `Ctrl+X` / `Shift+Delete` => cut
- `Ctrl+V` / `Shift+Insert` => paste
- `Ctrl+A` => select all

This applies to both single-line (`Entry`) and multiline (`Text`) fields.

