<?php
declare(strict_types=1);

namespace TalkPlatform;

class TalkAPIException extends \RuntimeException
{
    public function __construct(public int $status, public array $payload)
    {
        parent::__construct("Talk API error {$status}");
    }
}

class TalkClient
{
    public function __construct(private string $baseUrl, private ?string $apiKey = null, private int $timeout = 20)
    {
        $this->baseUrl = rtrim($baseUrl, '/');
    }

    public function request(string $method, string $path, ?array $payload = null): array
    {
        $headers = ['Accept: application/json', 'Content-Type: application/json'];
        if ($this->apiKey) $headers[] = 'X-Talk-API-Key: ' . $this->apiKey;
        $handle = curl_init($this->baseUrl . $path);
        curl_setopt_array($handle, [
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_POSTFIELDS => $payload === null ? null : json_encode($payload),
        ]);
        $raw = curl_exec($handle);
        $status = (int) curl_getinfo($handle, CURLINFO_HTTP_CODE);
        curl_close($handle);
        $data = json_decode((string) $raw, true) ?: [];
        if ($status < 200 || $status >= 300) throw new TalkAPIException($status, $data);
        return $data;
    }

    public function documents(string $query = ''): array { return $this->request('GET', '/api/v1/documents/' . ($query ? '?q=' . rawurlencode($query) : '')); }
    public function document(int $id): array { return $this->request('GET', "/api/v1/documents/{$id}/"); }
    public function updateDocument(int $id, array $payload): array { return $this->request('PATCH', "/api/v1/documents/{$id}/", $payload); }
    public function archiveDocument(int $id): array { return $this->request('DELETE', "/api/v1/documents/{$id}/"); }
    public function engagement(int $days = 30): array { return $this->request('GET', "/api/v1/analytics/engagement/?days={$days}"); }
    public function partner(): array { return $this->request('GET', '/api/v1/partner/me/'); }
    public function mobileSync(?string $lastSync = null): array { return $this->request('GET', '/api/mobile/sync/' . ($lastSync ? '?last_sync=' . rawurlencode($lastSync) : '')); }
    public function mobileEvents(array $events): array { return $this->request('POST', '/api/mobile/events/', ['events' => $events]); }
}
