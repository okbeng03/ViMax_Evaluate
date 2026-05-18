/**
 * E2E tests for history list page
 */

describe('History List Page', () => {
  beforeEach(() => {
    cy.visit('/history');
  });

  it('displays the history list page', () => {
    cy.contains('历史评估记录').should('be.visible');
  });

  it('shows loading state initially', () => {
    cy.get('.ant-spin').should('be.visible');
  });

  it('displays task table after loading', () => {
    cy.get('.ant-table').should('be.visible');
  });

  it('supports pagination', () => {
    cy.get('.ant-pagination').should('be.visible');
  });

  it('has filter controls', () => {
    cy.get('.ant-select').should('be.visible');
    cy.get('.ant-btn').contains('新建任务').should('be.visible');
  });

  it('navigates to detail page on task click', () => {
    cy.get('.ant-table-tbody .ant-btn-link').first().click();
    cy.url().should('include', '/evaluation/');
  });
});
