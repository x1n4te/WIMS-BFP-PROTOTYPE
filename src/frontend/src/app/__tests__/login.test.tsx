import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock('next/image', () => ({
  __esModule: true,
  default: (props: Record<string, unknown>) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ user: null, loading: false, login: vi.fn() }),
}));

describe('LoginPage (turnover build)', () => {
  it('offers only SSO sign-in: no register link, no return-to-public-site link, no navigation bar', async () => {
    const { default: LoginPage } = await import('../login/page');
    const { container } = render(<LoginPage />);

    expect(screen.getByRole('button', { name: /continue to secure sign-in/i })).toBeInTheDocument();
    expect(container.querySelector('a[href="/register"]')).not.toBeInTheDocument();
    expect(screen.queryByText(/create a reporter account/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId('login-return')).not.toBeInTheDocument();
    expect(container.querySelector('header')).not.toBeInTheDocument();
  });
});
