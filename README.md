# monopoly 2d implementation to learn panda3d

## build

```
python -m pygbag --archive --template noctx.tmpl --ume_block 0 main.py
```

## FSM configuration

The FSM loops over those states. A global variable `self.actor` is used to apply different behaviour while traversing the states.

![fsm states](./docs/fsm_guide.png)

## game mechanics

The game offers a variation of the classic monopoly game to make it more innovative to players. 

The variations are:
* different board sizes. size can be customized while starting
* asymmetric powers: each player has an unique ability. the ability can be chosen among the following:
** cheaper upgrades
** base income increased
* digital mini games: certain board spaces triggers quick mini games

## publish

Manually uploaded to [itch.io](https://pacman81.itch.io/monopoly-2d-prototype)

