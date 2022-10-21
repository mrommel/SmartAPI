import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from 'src/app/services/auth.service';
import { ApiService } from '../../services/api.service'

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  form: FormGroup
  constructor(
    private _api : ApiService,
    private _auth: AuthService,
    private router: Router,
    public fb: FormBuilder
  ) { }

  ngOnInit(): void {
    this.form = this.fb.group({
      username: ['mrommel@avm.de', Validators.required],
      password:['password123', Validators.required]
    });
  }

  login(): void {
    let b = this.form.value
    console.log(b)
    this._api.postTypeRequest('api/auth/login', b).subscribe((res: any) => {
      console.log(res)
      if(res.access_token){
        this._auth.setDataInLocalStorage('token', res.access_token)
        this.router.navigate(['profile'])
      }
    }, err => {
      console.log(err)
    });
  }
}
