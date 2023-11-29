// Refactored from https://github.com/Azure-Samples/ms-identity-javascript-react-tutorial/blob/main/1-Authentication/1-sign-in/SPA/src/authConfig.js

import { AuthenticationResult, IPublicClientApplication } from "@azure/msal-browser";

interface AuthSetup {
    // Set to true if login elements should be shown in the UI
    useLogin: boolean;
    loginRequest: {
        scopes: Array<string>;
    };
    tokenRequest: {
        scopes: Array<string>;
    };
}

// Fetch the auth setup JSON data from the API if not already cached
async function fetchAuthSetup(): Promise<AuthSetup> {
    const response = await fetch("/auth_setup");
    if (!response.ok) {
        throw new Error(`auth setup response was not ok: ${response.status}`);
    }
    return await response.json();
}

const authSetup = await fetchAuthSetup();

export const useLogin = authSetup.useLogin;

/**
 * Scopes you add here will be prompted for user consent during sign-in.
 * By default, MSAL.js will add OIDC scopes (openid, profile, email) to any login request.
 * For more information about OIDC scopes, visit:
 * https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent#openid-connect-scopes
 */
export const loginRequest = authSetup.loginRequest;

const tokenRequest = authSetup.tokenRequest;

// Build an absolute redirect URI using the current window's location and the relative redirect URI from auth setup
export const getRedirectUri = () => {
    return window.location.origin + "/redirect";
};

// Get an access token for use with the API server.
// ID token received when logging in may not be used for this purpose because it has the incorrect audience
export const getToken = (client: IPublicClientApplication): Promise<AuthenticationResult | undefined> => {
    return client
        .acquireTokenSilent({
            ...tokenRequest,
            redirectUri: getRedirectUri()
        })
        .catch(error => {
            console.log(error);
            return undefined;
        });
};
