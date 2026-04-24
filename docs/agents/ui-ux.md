# UI/UX Agent Guide

Use this guide for visual design, interaction design, copy, motion, and mobile product polish.

## Product Feel

bunq Bloom should feel bright, direct, and kid-friendly without becoming childish.

Design direction:

- light theme
- bunq-inspired rainbow accents
- green for earned/success
- blue for goals/progress
- yellow for warning/waiting
- red only for spending or hard failure
- large mobile tap targets
- clear camera-first journey

Avoid:

- generic SaaS dashboards
- dark-mode-first screens
- dense banking tables
- vague AI copy
- decorative motion that slows the core loop

## Mobile Baseline

Design for a 390px phone viewport first.

Minimum UX rules:

- tap targets at least 44px
- primary action visible without hunting
- one main decision per screen
- clear progress during AI/payment waits
- kid can recover from mistakes with retake/retry

## Core Interaction

The emotional product moment is:

```text
I did the work -> the app saw it -> I earned money -> my balance changed
```

Every UI decision should reinforce that loop.

## Copy

Write for kids aged 8-14 and parents.

Kid copy:

- short
- concrete
- encouraging but not fake
- specific about what changed

Parent copy:

- clear
- trustworthy
- focused on expectations, reward, and verification

Bad:

```text
AI verification completed successfully.
```

Better:

```text
Nice work. Your bed is made and the floor is clear.
```

## Completion Screen Requirements

The completion screen must show:

- AI verdict
- specific tags
- reward amount
- payment status
- updated kid balance
- next action

For fallback mode, copy must be explicit enough for honesty while keeping the flow usable.

## Cross-Agent Review Points

UI/UX should review these before they are considered done:

- camera capture and retake flow
- verification loading state
- payment loading state
- completion screen hierarchy
- AI rejection copy
- payment failure copy
- fake/local mode copy
- AI fallback copy
- bunq fallback copy
- recoverable error states

For cross-stack work, UI/UX should provide copy and state guidance early enough that frontend does not hardcode vague placeholders.

## Motion

Use motion sparingly:

- camera step transitions
- verification progress
- earned-money moment
- balance increase

Do not animate critical error messages away.
