import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  private url(path: string) { return `${environment.apiBaseUrl}${path}`; }

  get<T>(path: string, params?: Record<string, string | number>) {
    return this.http.get<T>(this.url(path), { params: params as any });
  }
  post<T>(path: string, body: unknown = {}) { return this.http.post<T>(this.url(path), body); }
  put<T>(path: string, body: unknown) { return this.http.put<T>(this.url(path), body); }
  patch<T>(path: string, body: unknown) { return this.http.patch<T>(this.url(path), body); }
  delete<T>(path: string) { return this.http.delete<T>(this.url(path)); }
}