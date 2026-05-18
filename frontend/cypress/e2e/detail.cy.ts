/**
 * E2E tests for evaluation detail page
 */

describe('Evaluation Detail Page', () => {
  const testTaskId = '550e8400-e29b-41d4-a716-446655440000';

  beforeEach(() => {
    cy.visit(`/evaluation/${testTaskId}`);
  });

  it('displays the detail page', () => {
    cy.contains('任务状态').should('be.visible');
  });

  it('shows loading state initially', () => {
    cy.get('.ant-spin').should('be.visible');
  });

  it('displays task ID', () => {
    cy.contains(testTaskId.slice(0, 8)).should('be.visible');
  });

  it('has back button', () => {
    cy.get('.ant-btn').contains('返回列表').should('be.visible');
  });

  it('navigates back to history on back click', () => {
    cy.get('.ant-btn').contains('返回列表').click();
    cy.url().should('include', '/history');
  });

  it('shows progress during processing', () => {
    cy.get('.ant-progress').should('be.visible');
  });
});
