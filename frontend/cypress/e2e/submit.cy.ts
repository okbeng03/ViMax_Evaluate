/**
 * E2E tests for task submission page
 */

describe('Task Submission Page', () => {
  beforeEach(() => {
    cy.visit('/submit');
  });

  it('displays the submission page', () => {
    cy.contains('提交图像评估任务').should('be.visible');
  });

  it('has form fields', () => {
    cy.get('.ant-form').should('be.visible');
    cy.contains('Prompt / 描述').should('be.visible');
  });

  it('has project selector', () => {
    cy.get('.ant-select').should('be.visible');
  });

  it('has image upload area', () => {
    cy.get('.ant-upload-drag').should('be.visible');
  });

  it('has submit button', () => {
    cy.contains('提交评估任务').should('be.visible');
  });

  it('validates prompt is required', () => {
    cy.contains('提交评估任务').click();
    cy.contains('请输入Prompt描述').should('be.visible');
  });

  it('validates image is required', () => {
    cy.get('textarea').type('A beautiful sunset');
    cy.contains('提交评估任务').click();
    cy.contains('请提供图片URL或上传图片').should('be.visible');
  });
});
