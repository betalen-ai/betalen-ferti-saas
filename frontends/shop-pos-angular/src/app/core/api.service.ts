import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  post<T>(path: string, body: unknown) {
    return this.http.post<T>(`${environment.apiBaseUrl}${path}`, body);
  }
}
