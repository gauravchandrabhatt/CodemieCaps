Feature: Assistant-led SDLC workflow with human approval
  The assistant can prepare artifacts, but only a human can unlock a later phase.

  Scenario: Approve a submitted gap analysis
    Given the gap analysis is waiting for human review
    When the reviewer approves it with a note
    Then the analysis phase is approved
    And the stories and plan phase becomes the current phase
    And the approval appears in the audit trail

  Scenario: Reject and revise an artifact
    Given the gap analysis is waiting for human review
    When the reviewer requests changes with a note
    Then the analysis remains the current phase
    And the assistant can resubmit a revised artifact

  Scenario: Prevent skipping a phase
    Given the gap analysis is waiting for human review
    When a test plan is submitted before its preceding phases are approved
    Then the workflow rejects the out-of-order change

  Scenario: Add an enhancement to the backlog
    When a reviewer creates a story with a title and priority
    Then the story is saved and receives a project key
