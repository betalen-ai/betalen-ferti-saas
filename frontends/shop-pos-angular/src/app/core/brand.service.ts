import { inject, Injectable } from "@angular/core";
import { Observable, throwError } from "rxjs";
import { Brand } from  '../models/shop.models';
import { ApiService } from "./api.service";
import { AuthService } from "./auth.service";

@Injectable({
    providedIn: "root",
})
export class BrandService {
   private api = inject(ApiService);
   private auth = inject(AuthService);

    getBrandsAsync(): Observable<Brand[]> {
        const tenantId = this.auth.tenantId();
        if (!tenantId) {
            return throwError(() => new Error("Cannot load brands without an authenticated tenant."));
        }
        return this.api.get<Brand[]>("/brands", {
            tenant_id: tenantId,
            include_inactive: "false",
            limit: 100,
            offset: 0,
        });
    }
}