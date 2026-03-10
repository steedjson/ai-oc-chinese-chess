import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../index';
import { useAuthStore } from '../../../stores/auth';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...(actual as any),
    useNavigate: () => mockNavigate,
  };
});

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 重置 auth store
    useAuthStore.setState({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it('should render login form', () => {
    renderWithRouter(<LoginPage />);

    expect(screen.getByText('中国象棋管理后台')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should display username input', () => {
    renderWithRouter(<LoginPage />);

    const usernameInput = screen.getByPlaceholderText('用户名');
    expect(usernameInput).toBeInTheDocument();
  });

  it('should display password input', () => {
    renderWithRouter(<LoginPage />);

    const passwordInput = screen.getByPlaceholderText('密码');
    expect(passwordInput).toBeInTheDocument();
  });

  it('should disable form when loading', () => {
    useAuthStore.setState({ isLoading: true });
    
    renderWithRouter(<LoginPage />);

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');

    expect(usernameInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
  });

  it('should show loading button text when loading', () => {
    useAuthStore.setState({ isLoading: true });
    
    renderWithRouter(<LoginPage />);

    expect(screen.getByRole('button')).toHaveTextContent(/登录中/i);
  });

  it('should call login with credentials on form submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(useAuthStore.getState(), 'login').mockImplementation(mockLogin);

    renderWithRouter(<LoginPage />);

    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const submitButton = screen.getByRole('button');

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('should clear error on mount if error exists', () => {
    const mockClearError = vi.fn();
    vi.spyOn(useAuthStore.getState(), 'clearError').mockImplementation(mockClearError);
    
    useAuthStore.setState({ error: 'Previous error' });
    
    renderWithRouter(<LoginPage />);

    expect(mockClearError).toHaveBeenCalled();
  });

  it('should display chess emoji icon', () => {
    renderWithRouter(<LoginPage />);

    expect(screen.getByText('♟️')).toBeInTheDocument();
  });
});
