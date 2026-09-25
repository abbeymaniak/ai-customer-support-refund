import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { CustomerUser, CustomerLoginCredentials } from '../types';
import { customerAuthApi } from '../api/customerAuth';

interface CustomerAuthContextType {
  customer: CustomerUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: CustomerLoginCredentials) => Promise<CustomerUser>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const CustomerAuthContext = createContext<CustomerAuthContextType | undefined>(undefined);

export const CustomerAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [customer, setCustomer] = useState<CustomerUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshProfile = useCallback(async () => {
    try {
      const profile = await customerAuthApi.getMe();
      setCustomer(profile);
    } catch {
      setCustomer(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  const login = async (credentials: CustomerLoginCredentials): Promise<CustomerUser> => {
    setIsLoading(true);
    try {
      const loggedInCustomer = await customerAuthApi.login(credentials);
      setCustomer(loggedInCustomer);
      return loggedInCustomer;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await customerAuthApi.logout();
    } finally {
      setCustomer(null);
    }
  };

  return (
    <CustomerAuthContext.Provider
      value={{
        customer,
        isLoading,
        isAuthenticated: !!customer,
        login,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </CustomerAuthContext.Provider>
  );
};

const defaultCustomerAuth: CustomerAuthContextType = {
  customer: null,
  isLoading: false,
  isAuthenticated: false,
  login: async () => {
    throw new Error('CustomerAuthProvider required');
  },
  logout: async () => {},
  refreshProfile: async () => {},
};

export const useCustomerAuth = (): CustomerAuthContextType => {
  const context = useContext(CustomerAuthContext);
  return context || defaultCustomerAuth;
};
