<script>
    import { onMount } from 'svelte';
    import { browser } from '$app/env';

    let userData = null;
    let error = null;

    onMount(async () => {
        if (browser) {
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');

            if (code) {
                try {
                    const response = await fetch(`http://localhost:8000/api/user/login/kakao/callback?code=${code}`);
                    const data = await response.json();
                    if (response.ok) {
                        userData = data;
                    } else {
                        throw new Error(data.message || 'Failed to login with Kakao');
                    }
                } catch (err) {
                    error = err.message;
                }
            }
        }
    });
</script>

{#if error}
    <p class="error">Error: {error}</p>
{:else if userData}
    <div>
        <h1>Welcome, {userData.user_data.properties.nickname}!</h1>
        <p>Your email is {userData.user_data.kakao_account.email}.</p>
    </div>
{:else}
    <p>Processing login...</p>
{/if}

<style>
    .error {
        color: red;
    }
</style>
