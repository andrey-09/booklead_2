^9::{
Loop{
Loop 5{
;for each tab
MouseClick "left", 800, 400,1,80
Sleep 60000
}
;each second 2 times ctrl tab
if Mod(A_Index,2)<1
{
Send "^{Tab}"
Sleep 1000
Send "^{Tab}"
}else{
Send "^{Tab}"
}
}
}
Esc::Reload  

^Esc::ExitApp