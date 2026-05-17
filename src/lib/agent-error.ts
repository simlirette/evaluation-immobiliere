/**
 * Converts any thrown value from an agent API call into a user-visible
 * French error message suitable for display in the chat reply list.
 */
export function formatAgentError(err: unknown): string {
  if (err instanceof Error) {
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      return "Erreur réseau — vérifier la connexion et réessayer."
    }
    if (err.message.includes('timeout') || err.message.includes('Timeout')) {
      return "L'agent n'a pas répondu dans le délai imparti. Réessayer."
    }
    if (err.message.includes('401') || err.message.includes('403')) {
      return "Accès refusé — session expirée ou non autorisée."
    }
    if (err.message.includes('500') || err.message.includes('502') || err.message.includes('503')) {
      return "Le serveur a retourné une erreur. Réessayer dans quelques instants."
    }
    if (err.message) {
      return `Erreur agent\u00a0: ${err.message}`
    }
  }
  return "Une erreur inattendue s\u2019est produite. Réessayer."
}
